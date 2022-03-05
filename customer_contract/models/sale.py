# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    show_customer_contract_line = fields.Boolean(compute='_compute_show_contract_line')

    def _compute_show_contract_line(self):
        super(SaleOrder, self)._compute_show_contract_line()
        for order in self:
            count = False
            if order.partner_id:
                count = self.env['customer.contract.line'].search_count([
                    ('contract_id.expiration_date', '>', fields.Datetime.now()),
                    ('contract_id.partner_ids', 'in', order.partner_id.ids),
                    ('remaining_qty', '>', 0.0),
                    ('state', '=', 'confirmed')
                ])

            order.show_customer_contract_line = bool(count)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    customer_contract_line_id = fields.Many2one('customer.contract.line', string="Customer Contract Applicable")

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id and self.customer_contract_line_id and self.customer_contract_line_id.product_id != self.product_id:
            raise ValidationError(
                "product %s is not belongs to contract %s" % (self.product_id.display_name, self.customer_contract_line_id.contract_id.name))

    @api.onchange('customer_contract_line_id')
    def onchange_customer_contract(self):
        if self.customer_contract_line_id:
            self.product_id = self.customer_contract_line_id.product_id

    @api.onchange('order_partner_id', 'customer_contract_line_id')
    def onchange_customer_id(self):
        """
        Return domain for customer_contract_line_id 
        """
        if self.order_partner_id:
            contract_ids = self.env['customer.contract.line'].search([
                ('contract_id.expiration_date', '>', fields.Datetime.now()),
                ('contract_id.partner_ids', 'in', self.order_partner_id.ids),
                ('remaining_qty', '>', 0.0),
                ('state', '=', 'confirmed')
            ])
            domain = [('id', 'in', contract_ids.ids)]
            return {'domain': {'customer_contract_line_id': domain}}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
