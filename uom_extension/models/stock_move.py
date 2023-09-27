# -*- coding: utf-8 -*-

from collections import defaultdict

from odoo import models, fields, api, _
from odoo.tools.float_utils import float_round, float_is_zero
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self._context.get('check_uom_change', None):
            args += [('state', 'in', ['draft'])]
        return super(StockMove, self).search(args, offset, limit, order, count=count)

    def wrapper_action_done_inventory(self):
        self._action_done()
        return True

    """
        overridden methods from stock_account to fix journal entry issues related to uom change
    """

    def _create_in_svl(self, forced_quantity=None):
        """Create a `stock.valuation.layer` from `self`.

        :param forced_quantity: under some circunstances, the quantity to value is different than
            the initial demand of the move (Default value = None)
        Note - conversion done to ppt_uom_id to correct stock journal entries
        """
        svl_vals_list = []
        for move in self:
            move = move.with_company(move.company_id)
            valued_move_lines = move._get_in_move_lines()
            valued_quantity = 0
            for valued_move_line in valued_move_lines:
                valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done,
                                                                                     move.product_id.ppt_uom_id)
            unit_cost = abs(move._get_price_unit())  # May be negative (i.e. decrease an out move).
            if move.product_id.cost_method == 'standard':
                unit_cost = move.product_id.standard_price
            svl_vals = move.product_id._prepare_in_svl_vals(forced_quantity or valued_quantity, unit_cost)
            svl_vals.update(move._prepare_common_svl_vals())
            if forced_quantity:
                svl_vals[
                    'description'] = 'Correction of %s (modification of past move)' % move.picking_id.name or move.name
            svl_vals_list.append(svl_vals)
        return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

    def _create_out_svl(self, forced_quantity=None):
        """Create a `stock.valuation.layer` from `self`.

        :param forced_quantity: under some circumstances, the quantity to value is different than
            the initial demand of the move (Default value = None)
        Note - conversion done to ppt_uom_id to correct stock journal entries
        """
        svl_vals_list = []
        for move in self:
            move = move.with_company(move.company_id)
            valued_move_lines = move._get_out_move_lines()
            valued_quantity = 0
            for valued_move_line in valued_move_lines:
                valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done,
                                                                                     move.product_id.ppt_uom_id or move.product_id.uom_id)
            if float_is_zero(forced_quantity or valued_quantity,
                             precision_rounding=move.product_id.ppt_uom_id.rounding or move.product_id.uom_id.rounding):
                continue
            svl_vals = move.product_id._prepare_out_svl_vals(forced_quantity or valued_quantity, move.company_id)
            svl_vals.update(move._prepare_common_svl_vals())
            if forced_quantity:
                svl_vals[
                    'description'] = 'Correction of %s (modification of past move)' % move.picking_id.name or move.name
            svl_vals['description'] += svl_vals.pop('rounding_adjustment', '')
            svl_vals_list.append(svl_vals)
        return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

    def _create_dropshipped_svl(self, forced_quantity=None):
        """Create a `stock.valuation.layer` from `self`.

        :param forced_quantity: under some circunstances, the quantity to value is different than
            the initial demand of the move (Default value = None)
        Note - conversion done to ppt_uom_id to correct stock journal entries
        """
        svl_vals_list = []
        for move in self:
            move = move.with_company(move.company_id)
            valued_move_lines = move.move_line_ids
            valued_quantity = 0
            for valued_move_line in valued_move_lines:
                valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done,
                                                                                     move.product_id.ppt_uom_id)
            quantity = forced_quantity or valued_quantity

            unit_cost = move._get_price_unit()
            if move.product_id.cost_method == 'standard':
                unit_cost = move.product_id.standard_price

            common_vals = dict(move._prepare_common_svl_vals(), remaining_qty=0)

            # create the in if it does not come from a valued location (eg subcontract -> customer)
            if not move.location_id._should_be_valued():
                in_vals = {
                    'unit_cost': unit_cost,
                    'value': unit_cost * quantity,
                    'quantity': quantity,
                }
                in_vals.update(common_vals)
                svl_vals_list.append(in_vals)

            # create the out if it does not go to a valued location (eg customer -> subcontract)
            if not move.location_dest_id._should_be_valued():
                out_vals = {
                    'unit_cost': unit_cost,
                    'value': unit_cost * quantity * -1,
                    'quantity': quantity * -1,
                }
                out_vals.update(common_vals)
                svl_vals_list.append(out_vals)

        return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

    def _prepare_analytic_line(self):
        """overridden to fix uom change issue"""
        self.ensure_one()
        if not self._get_analytic_account():
            return False

        if self.state in ['cancel', 'draft']:
            return False

        if self.state != 'done':
            unit_amount = self.product_uom._compute_quantity(
                self.quantity_done, self.product_id.ppt_uom_id)
            # Falsy in FIFO but since it's an estimation we don't require exact correct cost. Otherwise
            # we would have to recompute all the analytic estimation at each out.
            amount = - unit_amount * self.product_id.standard_price
        elif self.product_id.valuation == 'real_time':
            accounts_data = self.product_id.product_tmpl_id.get_product_accounts()
            account_valuation = accounts_data.get('stock_valuation', False)
            analytic_line_vals = self.stock_valuation_layer_ids.account_move_id.line_ids.filtered(
                lambda l: l.account_id == account_valuation)._prepare_analytic_line()
            amount = - sum(vals['amount'] for vals in analytic_line_vals)
            unit_amount = - sum(vals['unit_amount'] for vals in analytic_line_vals)
        elif sum(self.stock_valuation_layer_ids.mapped('quantity')):
            amount = sum(self.stock_valuation_layer_ids.mapped('value'))
            unit_amount = - sum(self.stock_valuation_layer_ids.mapped('quantity'))
        if self.analytic_account_line_id:
            self.analytic_account_line_id.unit_amount = unit_amount
            self.analytic_account_line_id.amount = amount
            return False
        elif amount:
            return self._generate_analytic_lines_data(
                unit_amount, amount)

    def _generate_analytic_lines_data(self, unit_amount, amount):
        """overridden to fix uom change issue"""
        self.ensure_one()
        account_id = self._get_analytic_account()
        return {
            'name': self.name,
            'amount': amount,
            'account_id': account_id.id,
            'unit_amount': unit_amount,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_id.ppt_uom_id.id,
            'company_id': self.company_id.id,
            'ref': self._description,
            'category': 'other',
        }

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id,
                                       credit_account_id, description):
        # This method returns a dictionary to provide an easy extension hook to modify the valuation lines (see purchase for an example)
        """overridden to fix uom change issue"""
        self.ensure_one()
        debit_line_vals = {
            'name': description,
            'product_id': self.product_id.id,
            'quantity': qty,
            'product_uom_id': self.product_id.ppt_uom_id.id,
            'ref': description,
            'partner_id': partner_id,
            'debit': debit_value if debit_value > 0 else 0,
            'credit': -debit_value if debit_value < 0 else 0,
            'account_id': debit_account_id,
        }

        credit_line_vals = {
            'name': description,
            'product_id': self.product_id.id,
            'quantity': qty,
            'product_uom_id': self.product_id.ppt_uom_id.id,
            'ref': description,
            'partner_id': partner_id,
            'credit': credit_value if credit_value > 0 else 0,
            'debit': -credit_value if credit_value < 0 else 0,
            'account_id': credit_account_id,
        }

        rslt = {'credit_line_vals': credit_line_vals, 'debit_line_vals': debit_line_vals}
        if credit_value != debit_value:
            # for supplier returns of product in average costing method, in anglo saxon mode
            diff_amount = debit_value - credit_value
            price_diff_account = self.product_id.property_account_creditor_price_difference

            if not price_diff_account:
                price_diff_account = self.product_id.categ_id.property_account_creditor_price_difference_categ
            if not price_diff_account:
                raise UserError(
                    _('Configuration error. Please configure the price difference account on the product or its category to process this operation.'))

            rslt['price_diff_line_vals'] = {
                'name': self.name,
                'product_id': self.product_id.id,
                'quantity': qty,
                'product_uom_id': self.product_id.ppt_uom_id.id,
                'ref': description,
                'partner_id': partner_id,
                'credit': diff_amount > 0 and diff_amount or 0,
                'debit': diff_amount < 0 and -diff_amount or 0,
                'account_id': price_diff_account.id,
            }
        return rslt

    # def _get_price_unit(self):
    #     """ Returns the unit price for the move"""
    #     """overridden to fix uom change issue"""
    #     self.ensure_one()
    #     # uom conversion moves takes the unit cost wrong
    #     if self.is_inventory and self.name == 'Product Quantity Confirmed RPC Call':
    #         return self.product_uom._compute_price(self.price_unit or self.product_id.standard_price, self.product_id.uom_id)
    #
    #     if not self.origin_returned_move_id and self.purchase_line_id and self.product_id.id == self.purchase_line_id.product_id.id:
    #         price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')
    #         line = self.purchase_line_id
    #         order = line.order_id
    #         price_unit = line.price_unit
    #         if line.taxes_id:
    #             qty = line.product_qty or 1
    #             price_unit = line.taxes_id.with_context(round=False).compute_all(price_unit, currency=line.order_id.currency_id, quantity=qty)['total_void']
    #             price_unit = float_round(price_unit / qty, precision_digits=price_unit_prec)
    #         if line.product_uom.id != line.product_id.ppt_uom_id.id:
    #             price_unit *= line.product_uom.factor / line.product_id.ppt_uom_id.factor
    #         if order.currency_id != order.company_id.currency_id:
    #             # The date must be today, and not the date of the move since the move move is still
    #             # in assigned state. However, the move date is the scheduled date until move is
    #             # done, then date of actual move processing. See:
    #             # https://github.com/odoo/odoo/blob/2f789b6863407e63f90b3a2d4cc3be09815f7002/addons/stock/models/stock_move.py#L36
    #             price_unit = order.currency_id._convert(
    #                 price_unit, order.company_id.currency_id, order.company_id, fields.Date.context_today(self), round=False)
    #         return price_unit
    #     return super(StockMove, self)._get_price_unit()

    def _get_price_unit(self):
        """ Returns the unit price for the move"""
        """overridden to fix uom change issue"""
        self.ensure_one()
        # uom conversion moves takes the unit cost wrong
        if self.is_inventory and self.name == 'Product Quantity Confirmed RPC Call':
            return self.product_uom._compute_price(self.price_unit or self.product_id.standard_price,
                                                   self.product_id.uom_id)
        if not self.origin_returned_move_id and self.purchase_line_id and self.product_id.id == self.purchase_line_id.product_id.id:
            price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')
            line = self.purchase_line_id
            order = line.order_id
            price_unit = line.price_unit
            if line.taxes_id:
                qty = line.product_qty or 1
                price_unit = \
                line.taxes_id.with_context(round=False).compute_all(price_unit, currency=line.order_id.currency_id,
                                                                    quantity=qty)['total_void']
                price_unit = float_round(price_unit / qty, precision_digits=price_unit_prec)
            if line.product_uom.id != line.product_id.ppt_uom_id.id:
                price_unit *= line.product_uom.factor / line.product_id.ppt_uom_id.factor
            if order.currency_id != order.company_id.currency_id:
                # The date must be today, and not the date of the move since the move move is still
                # in assigned state. However, the move date is the scheduled date until move is
                # done, then date of actual move processing. See:
                # https://github.com/odoo/odoo/blob/2f789b6863407e63f90b3a2d4cc3be09815f7002/addons/stock/models/stock_move.py#L36
                price_unit = order.currency_id._convert(
                    price_unit, order.company_id.currency_id, order.company_id, fields.Date.context_today(self),
                    round=False)
            return price_unit

        """ Override to return RMA moves's price"""
        if self.picking_id and self.picking_id.rma_id:
            original_move = self.sale_line_id.move_ids.filtered(lambda r: r.picking_code == 'outgoing')
            if original_move:
                layers = original_move.sudo().stock_valuation_layer_ids
                if layers:
                    quantity = sum(layers.mapped("quantity"))
                    if not float_is_zero(quantity, precision_rounding=layers.uom_id.rounding):
                        return layers.currency_id.round(sum(layers.mapped("value")) / quantity)

        """ Returns the unit price to value this stock move """
        price_unit = self.price_unit
        precision = self.env['decimal.precision'].precision_get('Product Price')
        # If the move is a return, use the original move's price unit.
        if self.origin_returned_move_id and self.origin_returned_move_id.sudo().stock_valuation_layer_ids:
            layers = self.origin_returned_move_id.sudo().stock_valuation_layer_ids
            layers |= layers.stock_valuation_layer_ids
            quantity = sum(layers.mapped("quantity"))
            return layers.currency_id.round(sum(layers.mapped("value")) / quantity) if not float_is_zero(quantity,
                                                                                                         precision_rounding=layers.uom_id.rounding) else 0
        return price_unit if not float_is_zero(price_unit,
                                               precision) or self._should_force_price_unit() else self.product_id.standard_price

    @api.depends('product_id', 'product_uom_qty', 'product_uom')
    def _cal_move_weight(self):
        moves_with_weight = self.filtered(lambda moves: moves.product_id.weight > 0.00)
        for move in moves_with_weight:
            quantity_in_ppt_uom_id = move.product_id.uom_id._compute_quantity(move.product_qty,
                                                                              move.product_id.ppt_uom_id or move.product_id.uom_id)
            move.weight = (quantity_in_ppt_uom_id * move.product_id.weight)
        (self - moves_with_weight).weight = 0
