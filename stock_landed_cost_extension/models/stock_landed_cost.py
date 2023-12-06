# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero

class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    vendor_bill_ids = fields.Many2many(comodel_name='account.move', relation='account_move_stock_landed_cost_rel',
                                       column1='landed_cost_id', column2='vendor_bill_id')

    def get_valuation_lines(self):
        self.ensure_one()
        lines = []
        for move in self._get_targeted_move_ids():
            # it doesn't make sense to make a landed cost for a product that isn't set as being valuated in real time at real cost
            if move.product_id.cost_method not in ('fifo', 'average') or move.state == 'cancel' or not move.product_qty:
                continue
            ppt_quantity = move.product_qty
            if move.product_id.ppt_uom_id:
                ppt_quantity = move.product_id.uom_id._compute_quantity(move.product_qty,
                                                                  move.product_id.ppt_uom_id,
                                                                  rounding_method='HALF-UP')
            vals = {
                'product_id': move.product_id.id,
                'move_id': move.id,
                'quantity': ppt_quantity,
                'former_cost': sum(move.stock_valuation_layer_ids.mapped('value')),
                'weight': move.product_id.weight * ppt_quantity,
                'volume': move.product_id.volume * ppt_quantity
            }
            lines.append(vals)
        if not lines:
            target_model_descriptions = dict(self._fields['target_model']._description_selection(self.env))
            raise UserError(_("You cannot apply landed costs on the chosen %s(s). Landed costs can only be applied for products with FIFO or average costing method.", target_model_descriptions[self.target_model]))
        return lines

    def button_validate(self):
        self._check_can_validate()
        cost_without_adjusment_lines = self.filtered(lambda c: not c.valuation_adjustment_lines)
        if cost_without_adjusment_lines:
            cost_without_adjusment_lines.compute_landed_cost()
        if not self._check_sum():
            raise UserError(_('Cost and adjustments lines do not match. You should maybe recompute the landed costs.'))

        for cost in self:
            cost = cost.with_company(cost.company_id)
            move = self.env['account.move']
            move_vals = {
                'journal_id': cost.account_journal_id.id,
                'date': cost.date,
                'ref': cost.name,
                'line_ids': [],
                'move_type': 'entry',
            }
            valuation_layer_ids = []
            cost_to_add_byproduct = defaultdict(lambda: 0.0)
            for line in cost.valuation_adjustment_lines.filtered(lambda line: line.move_id):
                remaining_qty = sum(line.move_id.stock_valuation_layer_ids.mapped('remaining_qty'))
                linked_layer = line.move_id.stock_valuation_layer_ids[:1]

                ppt_quantity = line.move_id.product_qty
                if line.move_id.product_id.ppt_uom_id:
                    ppt_quantity = line.move_id.product_id.uom_id._compute_quantity(line.move_id.product_qty,
                                                                      line.move_id.product_id.ppt_uom_id,
                                                                      rounding_method='HALF-UP')
                # Prorate the value at what's still in stock
                cost_to_add = (remaining_qty / ppt_quantity) * line.additional_landed_cost
                if not cost.company_id.currency_id.is_zero(cost_to_add):
                    valuation_layer = self.env['stock.valuation.layer'].create({
                        'value': cost_to_add,
                        'unit_cost': 0,
                        'quantity': 0,
                        'remaining_qty': 0,
                        'stock_valuation_layer_id': linked_layer.id,
                        'description': cost.name,
                        'stock_move_id': line.move_id.id,
                        'product_id': line.move_id.product_id.id,
                        'stock_landed_cost_id': cost.id,
                        'company_id': cost.company_id.id,
                    })
                    linked_layer.remaining_value += cost_to_add
                    valuation_layer_ids.append(valuation_layer.id)
                # Update the AVCO
                product = line.move_id.product_id
                if product.cost_method == 'average':
                    cost_to_add_byproduct[product] += cost_to_add
                # Products with manual inventory valuation are ignored because they do not need to create journal entries.
                if product.valuation != "real_time":
                    continue
                # `remaining_qty` is negative if the move is out and delivered proudcts that were not
                # in stock.
                qty_out = 0
                if line.move_id._is_in():
                    qty_out = ppt_quantity - remaining_qty
                elif line.move_id._is_out():
                    qty_out = ppt_quantity
                move_vals['line_ids'] += line._create_accounting_entries(move, qty_out)

            # batch standard price computation avoid recompute quantity_svl at each iteration
            products = self.env['product.product'].browse(p.id for p in cost_to_add_byproduct.keys())
            for product in products:  # iterate on recordset to prefetch efficiently quantity_svl
                if not float_is_zero(product.quantity_svl, precision_rounding=product.uom_id.rounding):
                    product.with_company(cost.company_id).sudo().with_context(disable_auto_svl=True).standard_price += cost_to_add_byproduct[product] / product.quantity_svl

            move_vals['stock_valuation_layer_ids'] = [(6, None, valuation_layer_ids)]
            # We will only create the accounting entry when there are defined lines (the lines will be those linked to products of real_time valuation category).
            cost_vals = {'state': 'done'}
            if move_vals.get("line_ids"):
                move = move.create(move_vals)
                cost_vals.update({'account_move_id': move.id})
            cost.write(cost_vals)
            if cost.account_move_id:
                move._post()

            if cost.vendor_bill_id and cost.vendor_bill_id.state == 'posted' and cost.company_id.anglo_saxon_accounting:
                all_amls = cost.vendor_bill_id.line_ids | cost.account_move_id.line_ids
                for product in cost.cost_lines.product_id:
                    accounts = product.product_tmpl_id.get_product_accounts()
                    input_account = accounts['stock_input']
                    all_amls.filtered(lambda aml: aml.account_id == input_account and not aml.reconciled).reconcile()

            if cost.vendor_bill_ids:
                for bill in cost.vendor_bill_ids:
                    if bill.state == 'posted' and cost.company_id.anglo_saxon_accounting:
                        all_amls = bill.line_ids | cost.account_move_id.line_ids
                        for product in cost.cost_lines.product_id:
                            accounts = product.product_tmpl_id.get_product_accounts()
                            input_account = accounts['stock_input']
                            all_amls.filtered(lambda aml: aml.account_id == input_account and not aml.reconciled).reconcile()

        return True

class StockLandedCostLine(models.Model):
    _inherit = 'stock.landed.cost.lines'

    move_line_id = fields.Many2one('account.move.line', 'Invoice Line')
    move_id = fields.Many2one('account.move', 'Invoice', related="move_line_id.move_id")
