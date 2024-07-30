# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = 'stock.move'

    picking_partner_id = fields.Many2one('res.partner', related='picking_id.partner_id', string='Partner')
    is_storage_contract = fields.Boolean(compute='_compute_is_storage_contract', store=True)
    po_original_qty = fields.Float(related="purchase_line_id.product_uom_qty", string='Original Quantity (PO)',
                                   readonly=True)

    def product_price_update_before_done(self, forced_qty=None):
        pass

    @api.depends('sale_line_id.storage_contract_line_id', 'sale_line_id.order_id.storage_contract')
    def _compute_is_storage_contract(self):
        for line in self:
            if line.sale_line_id:
                line.is_storage_contract = True if line.sale_line_id.storage_contract_line_id else True if line.sale_line_id.order_id.storage_contract else False

    def _search_picking_for_assignation_domain(self):
        """
        Override to create one DO per one SO.
        """
        res = super()._search_picking_for_assignation_domain()
        for domain in res:
            if domain[0] == 'location_id':
                res.remove(domain)
                res.remove('&')
        return res

    def _get_accounting_data_for_valuation(self):
        """
        override to chnage account valuation of storage contract
        """
        journal_id, acc_src, acc_dest, acc_valuation = super(StockMove, self)._get_accounting_data_for_valuation()
        if self.is_storage_contract:
            acc_valuation = self.product_id.categ_id.sc_stock_valuation_account_id
            if not acc_valuation:
                raise UserError('Cannot find a SC Stock Valuation Account in product category: %s' % self.product_id.categ_id.name)
            acc_valuation = acc_valuation.id
        return journal_id, acc_src, acc_dest, acc_valuation

    def _get_src_account(self, accounts_data):
        if self._context.get('from_inv_adj', False) or self._context.get('is_scrap', False):
            acc_src = self.product_id.categ_id.inv_adj_input_account_id.id
            if not acc_src:
                raise UserError(
                    'Cannot find a Invenotry Adjustment stock input account for the product %s. You must define one on\
                     the product category, before processing this operation.' % self.product_id.display_name)
            return acc_src
        return super()._get_src_account(accounts_data)

    def _get_dest_account(self, accounts_data):
        if self._context.get('from_inv_adj', False) or self._context.get('is_scrap', False):
            acc_dest = self.product_id.categ_id.inv_adj_output_account_id.id
            if not acc_dest:
                raise UserError(
                    'Cannot find a Invenotry Adjustment stock output account for the product %s. You must define one on\
                     the product category, before processing this operation.' % self.product_id.display_name)
            return acc_dest
        return super()._get_dest_account(accounts_data)


StockMove()


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    picking_partner_id = fields.Many2one('res.partner', related='move_id.picking_partner_id', string='Partner')
    product_onhand_qty = fields.Float(string='Product Onhand QTY')


StockMoveLine()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
