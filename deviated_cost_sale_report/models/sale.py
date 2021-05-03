# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    vendor_id = fields.Many2one('res.partner', string="Vendor")
    rebate_contract_id = fields.Many2one('deviated.cost.contract', string="Rebate Contract Applicable")
    product_cost = fields.Float(string='Cost', digits=dp.get_precision('Product Price'))

    @api.multi
    def compute_vendor(self):
        """
        Set the vendor of selected product in sale order line
        (for the purpose of sorting lines based on vendor
        when generating reports)
        """

        vendor_id = False
        if self.product_id and self.order_partner_id and bool(
                self.order_partner_id.mapped('deviated_contract_ids.partner_product_ids').filtered(
                        lambda rec: rec.product_id.id == self.product_id.id)):
            vendor_id = self.product_id.seller_ids and self.product_id.seller_ids[0].name.id or False
        return vendor_id


    @api.multi
    def calculate_unit_price_and_contract(self):
        """
        Calculate the unit price of product by
        checking if the product included in any of the
        contracts of selected partner.if so,return deviated cost
        as unit price(least cost if product included
        in multiple contracts)and contract id.
        """
        unit_price = 0
        contract_id = False
        for record in self:
            contract_ids = record.order_partner_id.deviated_contract_ids.filtered(
                lambda rec: rec.expiration_date > datetime.now())
            for contract in contract_ids:
                contract_product_cost_id = contract.partner_product_ids.filtered(
                    lambda rec: rec.product_id.id == record.product_id.id)
                if contract_product_cost_id and contract_product_cost_id.cost < unit_price or not unit_price:
                    unit_price = contract_product_cost_id.cost
                    contract_id = contract.id if contract_product_cost_id else False
        return unit_price, contract_id

    @api.multi
    def calculate_customer_price(self):
        """
        Overrride the method to update msg if the product
        belongs to any contract of the selected partner
        """
        msg, product_price, price_from = super(SaleOrderLine, self).calculate_customer_price()
        if self.rebate_contract_id:
            msg = "Unit price of this product is fetched from the contract '%s'" % (self.rebate_contract_id.name)
        return msg, product_price, price_from

    @api.multi
    def compute_rebate_contract(self):
        """
        Set the contract_id in sale order line
        (for the purpose of sorting lines based on contract
        when generating reports)
        """
        contract_id = self.calculate_unit_price_and_contract()[1]
        rebate_contract_id = contract_id if self.product_id else False
        return rebate_contract_id

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        """
        Set the unit price of product
        as per the contracts of selected partner
        """
        res = super(SaleOrderLine, self).product_uom_change()
        unit_price = self.calculate_unit_price_and_contract()[0]
        if unit_price:
            self.price_unit = unit_price
            self.lst_price = unit_price
            self.working_cost = unit_price
        if self.product_id:
            self.product_cost = self.product_id.standard_price
        return res

    @api.onchange('product_id')
    def product_id_change(self):
        """
        Set the unit price of product
        as per the contracts of selected partner
        """
        res = super(SaleOrderLine, self).product_id_change()
        unit_price = self.calculate_unit_price_and_contract()[0]
        if unit_price:
            res.update({'value': {'price_unit': unit_price}})
        if self.product_id:
            self.product_cost = self.product_id.standard_price
            self.rebate_contract_id = self.compute_rebate_contract()
            self.vendor_id = self.compute_vendor()
        return res

    @api.depends('product_id', 'product_uom')
    def _compute_lst_cost_prices(self):
        res = super(SaleOrderLine, self)._compute_lst_cost_prices()
        self.rebate_contract_id = self.compute_rebate_contract()
        self.vendor_id = self.compute_vendor()
        unit_price = self.calculate_unit_price_and_contract()[0]
        if unit_price:
            self.lst_price = unit_price
            self.working_cost = unit_price


SaleOrderLine()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
