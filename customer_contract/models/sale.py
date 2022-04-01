# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from odoo.exceptions import ValidationError, UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    show_customer_contract_line = fields.Boolean('Has customer contract', default=False, copy=False)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(SaleOrder, self).onchange_partner_id()
        if self.partner_id and not self.storage_contract:
            contract = self.env['customer.contract.line'].search([
                ('contract_id.expiration_date', '>', fields.Datetime.now()),
                ('contract_id.partner_ids', 'in', self.partner_id.ids),
                ('remaining_qty', '>', 0.0),
                ('state', '=', 'confirmed')])
            if contract:
                self.show_customer_contract_line = True
            else:
                self.show_customer_contract_line = False
        else:
            self.show_customer_contract_line = False


    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            lines = self.env['customer.contract.line'].search([
                '|', ('contract_id.expiration_date', '<', fields.Datetime.now()),
                ('contract_id.partner_ids', 'in', order.partner_id.ids),
                ('remaining_qty', '<=', 0.0),
                ('state', '=', 'confirmed')
            ])
            lines.mapped('contract_id').action_expire()
        return res

    def action_confirm(self):
        """
        Do
        """
        if self.show_customer_contract_line:
            for line in self.order_line.filtered(lambda r: r.customer_contract_line_id):
                if line.customer_contract_line_id.remaining_qty < line.product_uom_qty:
                    raise ValidationError('There is not enough quantity remaining in the contract %s for product %s. Please remove the line in order to confirm this Sales Order.'\
                     %(line.customer_contract_line_id.contract_id.name, line.product_id.name))
        return super(SaleOrder, self).action_confirm()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    customer_contract_line_id = fields.Many2one('customer.contract.line', string="Customer Contract Applicable")


    @api.onchange('customer_contract_line_id')
    def contract_line_id_change(self):
        domain = {}
        if not self.product_id:
            domain = {
                'domain': {'customer_contract_line_id': [
                    ('contract_id.expiration_date', '>', fields.Datetime.now()),
                    ('remaining_qty', '>', 0),
                    ('contract_id.partner_ids', 'in', self.order_id.partner_id.ids),
                    ('state', '=', 'confirmed')]}}
        if self.customer_contract_line_id:
            self.product_id = self.customer_contract_line_id.product_id
            self.product_uom = self.customer_contract_line_id.product_id.uom_id
            self.price_unit = self.customer_contract_line_id.price
        else:
            msg, product_price, price_from = super(SaleOrderLine, self).calculate_customer_price()
            self.price_unit = product_price
        return domain

    def calculate_customer_contract(self):
        """
        Calculate the unit price of product by
        checking if the product included in any of the
        contracts of selected partner.
        """
        unit_price = 0
        contract_id = False
        for record in self:
            contract_ids = record.order_partner_id.customer_contract_ids.filtered(
                lambda rec: rec.expiration_date > datetime.now())
            for contract in contract_ids:
                contract_product_cost_id = contract.product_line_ids.filtered(
                    lambda rec: rec.product_id.id == record.product_id.id and rec.remaining_qty > 0)
                if contract_product_cost_id:
                    unit_price = contract_product_cost_id.price
                    contract_id = contract_product_cost_id.id
                    break
        return unit_price, contract_id

    @api.onchange('product_id')
    def product_id_change(self):
        """
        Set the unit price of product
        as per the contracts of selected partner
        """
        res = super(SaleOrderLine, self).product_id_change()
        if self.product_id and self.order_id.show_customer_contract_line:
            unit_price, contract_id = self.calculate_customer_contract()
            if unit_price or contract_id:
                domain = [
                    ('contract_id.expiration_date', '>', fields.Datetime.now()),
                    ('product_id', '=', self.product_id.id),
                    ('remaining_qty', '>', 0),
                    ('contract_id.partner_ids', 'in', self.order_id.partner_id.ids),
                    ('state', '=', 'confirmed')]
                if res.get('domain', False):
                    res['domain']['customer_contract_line_id'] = domain
                else:
                    res['domain'] = {'customer_contract_line_id': domain}
                res.update({'value': {'price_unit': unit_price, 'customer_contract_line_id': contract_id}})
        return res

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        result = super(SaleOrderLine, self).product_uom_change()
        if self.customer_contract_line_id:
            self.price_unit = self.customer_contract_line_id.price
            remaining = self.customer_contract_line_id.remaining_qty
            if self.order_id.state == 'sale' and self._origin in self.customer_contract_line_id.sale_line_ids:
                remaining = self.customer_contract_line_id.remaining_qty + self._origin.product_uom_qty
            if self.product_uom_qty > remaining:
                warning_mess = {
                    'title': _('More than Customer Contract'),
                    'message': _(
                        'You are going to Sell more than in customer contract.Only %s is remaining in this contract.' % (remaining))
                }
                self.product_uom_qty = self._origin.product_uom_qty
                result.update({'warning': warning_mess})
        return result


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
