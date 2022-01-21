# -*- coding: utf-8 -*-

import datetime
from datetime import timedelta, date

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    grace_period = fields.Integer(help="Gives the number of days extended for the customer after defaulting payments.",
                                  string='Customer Grace Period')

class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    code = fields.Char(string='Code')


class AccountTax(models.Model):
    _inherit = "account.tax"

    code = fields.Char(string='Code')



# TODO: FIX THIS FOR ODOO-15 MIGRATION
# TODO: re-implement after account relation migration
class AccountMove(models.Model):
    _inherit = "account.move"

    gross_profit = fields.Monetary(compute='calculate_gross_profit', string='Predicted Profit')
    storage_down_payment = fields.Boolean(copy=False)
    discount_from_batch = fields.Float('WriteOff Discount')
    invoice_address_id = fields.Many2one('res.partner', string="Billing Address")


    @api.model
    def create(self, vals):
        if vals.get('move_type', '') != 'entry':
            self = self.with_context(tracking_disable=True)
        return super(AccountMove, self).create(vals)


    def _compute_show_reset_to_draft_button(self):
        res = super()._compute_show_reset_to_draft_button()
        for move in self:
            move.show_reset_to_draft_button = self.env.user.has_group('account.group_account_manager')
        return res

    @api.depends('invoice_line_ids.profit_margin')
    def calculate_gross_profit(self):
         """
         Compute the gross profit in invoice.
         """
         for invoice in self:
            pass


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    #TODO not used anywhere ported from old version
    date_maturity_grace = fields.Date(string='Grace period Date')

    profit_margin = fields.Monetary(compute='calculate_profit_margin', string="Profit Margin")
    #comment the below 2 lines while running sale order line import scripts
    lst_price = fields.Float(string='Standard Price', digits='Product Price', store=True,
                          compute='_compute_lst_cost_prices')
    working_cost = fields.Float(string='Working Cost', digits='Product Price', store=True,
                             compute='_compute_lst_cost_prices')
    is_storage_contract = fields.Boolean(compute='_compute_is_storage_contract', store=True)


    @api.depends('sale_line_ids.storage_contract_line_id', 'sale_line_ids.order_id.storage_contract')
    def _compute_is_storage_contract(self):
         for line in self:
            pass #TODO remove me

    @api.depends('product_id', 'price_unit', 'quantity')
    def calculate_profit_margin(self):
        """
        Calculate profit margin in account invoice
        """
    #TODO test this functionality working
        for line in self:
            if line.product_id and line.product_id.default_code in ['misc'] and not line.sale_line_ids:
                line.profit_margin = 0.0
            elif line.sale_line_ids and line.sale_line_ids.filtered(lambda rec: rec.is_delivery is True):
                line.profit_margin = sum(line.sale_line_ids.mapped('profit_margin'))

            if line.product_id and line.quantity > 0 and line.product_uom_id:
                if line.product_id == line.move_id.company_id.check_bounce_product:
                    line.profit_margin = 0
                    continue
                if line.sale_line_ids and len(line.sale_line_ids) == 1:
                    if line.quantity == line.sale_line_ids.product_uom_qty:
                        line.profit_margin = line.sale_line_ids.profit_margin
                    else:
                        if line.sale_line_ids.product_uom_qty == 0:
                            line.profit_margin = 0
                        else:
                            line.profit_margin = line.sale_line_ids.profit_margin * line.quantity / line.sale_line_ids.product_uom_qty
                    continue
                product_price = line.working_cost
                line_price = line.price_unit
                if line.product_id.uom_id == line.product_uom_id and line.quantity % 1 != 0.0:
                    numer = line.price_unit * line.quantity
                    denom = (int(line.quantity / 1.0) + (
                                (line.quantity % 1) * (100 + line.product_id.categ_id.repacking_upcharge) / 100))
                    line_price = round(numer / denom, 2)
                line.profit_margin = (line_price - product_price) * line.quantity

    def _compute_lst_cost_prices(self):
        return 0.0


class PaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    set_to_default = fields.Boolean(string='Default')
    order_type = fields.Selection([('purchase', 'Purchase'), ('sale', 'Sale')], string='Type')
    code = fields.Char(string='Code')
    # TODO:: remove discount_per,due_date,discount_per field from accounting_extension.
    due_days = fields.Integer(string='Discount Days')
    discount_per = fields.Float(string='Discount Percent')
    is_discount = fields.Boolean('Is Cash Discount', help="Check this box if this payment term is \
        a cash discount. If cash discount is used the remaining amount of the invoice will not be paid")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
