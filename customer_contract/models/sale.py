# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

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

    @api.onchange('customer_contract_line_id')
    def onchange_customer_contract_line_id(self):
        """
        Return domain for customer_contract_line_id 
        """
        if self.order_partner_id :
            contract_ids = self.env['customer.contract.line'].search([
                    ('contract_id.expiration_date', '>', fields.Datetime.now()),
                    ('contract_id.partner_ids', 'in', self.order_partner_id.ids),
                    ('remaining_qty', '>', 0.0),
                    ('state', '=', 'confirmed')
                ])
            domain = [('id','in',contract_ids.ids)]
            return {'domain': {'customer_contract_line_id': domain}}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
