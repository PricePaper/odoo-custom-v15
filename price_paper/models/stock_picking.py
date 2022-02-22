# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from collections import defaultdict
from datetime import datetime
from itertools import groupby
from odoo.tools import float_compare
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.stock.models.stock_rule import ProcurementException


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    over_processed = fields.Boolean(string='Over Processed', compute='_compute_over_processed')

    @api.depends('move_ids_without_package.po_original_qty', 'move_ids_without_package.is_storage_contract')
    def _compute_over_processed(self):
        for record in self:
            if any([move.po_original_qty < move.quantity_done for move in record.move_lines if
                    move.is_storage_contract and move.purchase_line_id]):
                record.over_processed = True
            else:
                record.over_processed = False

    def action_sc_sync_with_receipt(self):
        self.ensure_one()
        for line in self.move_lines:
            done_flag = False
            if line.is_storage_contract:
                if line.sale_line_id.order_id.state == 'done':
                    done_flag = True
                    line.sale_line_id.order_id.action_unlock()
                line.purchase_line_id.product_qty = line.quantity_done
                line.sale_line_id.write({'product_uom_qty': line.quantity_done, 'qty_delivered': line.quantity_done})
                if done_flag:
                    line.sale_line_id.order_id.action_done()
        backorder_pick = self.env['stock.picking'].search([('backorder_id', '=', self.id), ('state', '!=', 'cancel')])
        if backorder_pick:
            backorder_pick.action_cancel()
            self.message_post(
                body=_("Back order <em>%s</em> <b>cancelled</b>.") % (",".join([b.name or '' for b in backorder_pick])))
        self.over_processed = False

    def sync_over_processed(self):
        self.ensure_one()
        return {
            'name': 'Sync OverProcessed',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'res_id': self.id,
            'view_id': self.env.ref('price_paper.view_stock_move_over_processed_window').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def button_validate(self):
        self.ensure_one()
        result = super(StockPicking, self).button_validate()
        if self.picking_type_code == 'incoming':
            for line in self.move_lines:
                if line.is_storage_contract and line.purchase_line_id:
                    line.sale_line_id.qty_delivered = line.quantity_done
        return result


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _make_po_get_domain(self, company_id, values, partner):
        domain = super(StockRule, self)._make_po_get_domain(company_id, values, partner)
        if values.get('move_dest_ids', self.env['stock.move']).is_storage_contract:
            domain += (('storage_contract_po', '=', True),)
        elif values.get('orderpoint_id'):
            domain += (('storage_contract_po', '=', False), ('sale_order_ids', '=', False))
        return domain

    @api.model
    def _run_buy(self, procurements):
        """
        copy paste override to avoid adding lines to make2order PO
        """
        procurements_by_po_domain = defaultdict(list)
        errors = []
        for procurement, rule in procurements:

            # Get the schedule date in order to find a valid seller
            procurement_date_planned = fields.Datetime.from_string(procurement.values['date_planned'])

            supplier = False
            if procurement.values.get('supplierinfo_id'):
                supplier = procurement.values['supplierinfo_id']
            else:
                supplier = procurement.product_id.with_company(procurement.company_id.id)._select_seller(
                    partner_id=procurement.values.get("supplierinfo_name"),
                    quantity=procurement.product_qty,
                    date=procurement_date_planned.date(),
                    uom_id=procurement.product_uom)

            # Fall back on a supplier for which no price may be defined. Not ideal, but better than
            # blocking the user.
            supplier = supplier or procurement.product_id._prepare_sellers(False).filtered(
                lambda s: not s.company_id or s.company_id == procurement.company_id)[:1]

            if not supplier:
                msg = _(
                    'There is no matching vendor price to generate the purchase order for product %s (no vendor defined, minimum quantity not reached, dates not valid, ...). Go on the product form and complete the list of vendors.') % (
                          procurement.product_id.display_name)
                errors.append((procurement, msg))

            partner = supplier.name
            # we put `supplier_info` in values for extensibility purposes
            procurement.values['supplier'] = supplier
            procurement.values['propagate_cancel'] = rule.propagate_cancel

            domain = rule._make_po_get_domain(procurement.company_id, procurement.values, partner)
            procurements_by_po_domain[domain].append((procurement, rule))

        if errors:
            raise ProcurementException(errors)

        for domain, procurements_rules in procurements_by_po_domain.items():
            # Get the procurements for the current domain.
            # Get the rules for the current domain. Their only use is to create
            # the PO if it does not exist.
            procurements, rules = zip(*procurements_rules)
            # Get the set of procurement origin for the current domain.
            origins = set([p.origin for p in procurements])
            # Check if a PO exists for the current domain.
            po = False
            for order in self.env['purchase.order'].sudo().search([dom for dom in domain]):
                if procurements[0].values.get('orderpoint_id') and not order.sale_order_count:
                    po = order
                    break
            company_id = procurements[0].company_id
            if not po:
                positive_values = [p.values for p in procurements if
                                   float_compare(p.product_qty, 0.0, precision_rounding=p.product_uom.rounding) >= 0]
                if positive_values:
                    # We need a rule to generate the PO. However the rule generated
                    # the same domain for PO and the _prepare_purchase_order method
                    # should only uses the common rules's fields.
                    vals = rules[0]._prepare_purchase_order(company_id, origins, positive_values)
                    # The company_id is the same for all procurements since
                    # _make_po_get_domain add the company in the domain.
                    # We use SUPERUSER_ID since we don't want the current user to be follower of the PO.
                    # Indeed, the current user may be a user without access to Purchase, or even be a portal user.
                    po = self.env['purchase.order'].with_company(company_id).with_user(SUPERUSER_ID).create(vals)
            else:
                # If a purchase order is found, adapt its `origin` field.
                if po.origin:
                    missing_origins = origins - set(po.origin.split(', '))
                    if missing_origins:
                        po.write({'origin': po.origin + ', ' + ', '.join(missing_origins)})
                else:
                    po.write({'origin': ', '.join(origins)})

            procurements_to_merge = self._get_procurements_to_merge(procurements)
            procurements = self._merge_procurements(procurements_to_merge)

            po_lines_by_product = {}
            grouped_po_lines = groupby(
                po.order_line.filtered(lambda l: not l.display_type and l.product_uom == l.product_id.uom_po_id).sorted(
                    lambda l: l.product_id.id), key=lambda l: l.product_id.id)
            for product, po_lines in grouped_po_lines:
                po_lines_by_product[product] = self.env['purchase.order.line'].concat(*list(po_lines))
            po_line_values = []
            for procurement in procurements:
                po_lines = po_lines_by_product.get(procurement.product_id.id, self.env['purchase.order.line'])
                po_line = po_lines._find_candidate(*procurement)

                if po_line:
                    # If the procurement can be merge in an existing line. Directly
                    # write the new values on it.
                    vals = self._update_purchase_order_line(procurement.product_id,
                                                            procurement.product_qty, procurement.product_uom,
                                                            company_id,
                                                            procurement.values, po_line)
                    po_line.write(vals)
                else:
                    if float_compare(procurement.product_qty, 0,
                                     precision_rounding=procurement.product_uom.rounding) <= 0:
                        # If procurement contains negative quantity, don't create a new line that would contain negative qty
                        continue
                    # If it does not exist a PO line for current procurement.
                    # Generate the create values for it and add it to a list in
                    # order to create it in batch.
                    partner = procurement.values['supplier'].name
                    po_line_values.append(self.env['purchase.order.line']._prepare_purchase_order_line_from_procurement(
                        procurement.product_id, procurement.product_qty,
                        procurement.product_uom, procurement.company_id,
                        procurement.values, po))
            self.env['purchase.order.line'].sudo().create(po_line_values)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
