# -*- coding: utf-8 -*-

from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models, fields, registry, api, _
from odoo.tools.float_utils import float_compare
from odoo.exceptions import ValidationError, AccessError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    release_date = fields.Datetime(string='Release Date')
    total_volume = fields.Float(string="Total Order Volume", compute='_compute_total_weight_volume')
    total_weight = fields.Float(string="Total Order Weight", compute='_compute_total_weight_volume')
    purchase_default_message = fields.Html(related="company_id.purchase_default_message", readonly=True)
    total_qty = fields.Float(string="Total Order Quantity", compute='_compute_total_weight_volume')
    vendor_delay = fields.Integer(related='partner_id.delay', string="Vendor Lead Time", readonly=True)
    vendor_order_freq = fields.Integer(related='partner_id.order_freq', string="Vendor Order Frequency", readonly=True)
    state = fields.Selection(selection_add=[('received', 'Received')])
    pickup_address_id = fields.Many2one('res.partner', string="Delivery Address")
    sale_order_count = fields.Integer(string="Sale Order Count", readonly=True, compute='_compute_sale_order_count')


    @api.depends('order_line.sale_order_id')
    def _compute_sale_order_count(self):
        for rec in self:
            rec.sale_order_count = len(rec.order_line.mapped('sale_order_id').ids) or len(rec.order_line.mapped('move_dest_ids.sale_line_id.order_id').ids)

    # @api.onchange('partner_id', 'company_id')
    # def onchange_partner_id(self):
    #     result = super(PurchaseOrder, self).onchange_partner_id()
    #     if self.partner_id:
    #         addr = self.partner_id.child_ids.filtered(lambda r: r.type == 'delivery' and r.default_shipping)
    #         if addr:
    #             self.pickup_address_id = addr.id
    #         elif not addr:
    #             addr = self.partner_id.address_get(['delivery'])
    #             self.pickup_address_id = addr and addr.get('delivery')
    #         else:
    #             self.pickup_address_id = self.partner_id.id
    #
    #     return result



    @api.depends('order_line.product_id', 'order_line.product_qty')
    def _compute_total_weight_volume(self):
        for order in self:
            volume = 0
            weight = 0
            qty = 0
            for line in order.order_line:
                volume += line.gross_volume
                weight += line.gross_weight
                qty += line.product_qty
            order.total_volume = volume
            order.total_weight = weight
            order.total_qty = qty


    def action_view_sale_orders(self):

        pass
        return True

    def add_sale_history_to_po_line(self):
        return True


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    gross_volume = fields.Float(string="Gross Volume", compute='_compute_gross_weight_volume')
    gross_weight = fields.Float(string="Gross Weight", compute='_compute_gross_weight_volume')



    @api.depends('product_id.volume', 'product_id.weight')
    def _compute_gross_weight_volume(self):
        for line in self:
            volume = line.product_id.volume * line.product_qty
            weight = line.product_id.weight * line.product_qty
            line.gross_volume = volume
            line.gross_weight = weight

    def show_sales_history(self):
        return True



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
