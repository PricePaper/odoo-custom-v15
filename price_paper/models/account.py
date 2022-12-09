# -*- coding: utf-8 -*-

import datetime
from datetime import timedelta, date
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    grace_period = fields.Integer(help="Gives the number of days extended for the customer after defaulting payments.", string='Customer Grace Period')


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    code = fields.Char(string='Code')


class AccountTax(models.Model):
    _inherit = "account.tax"

    code = fields.Char(string='Code')

class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def _prepare_default_reversal(self, move):
        res = super(AccountMoveReversal, self)._prepare_default_reversal(move)
        if move.move_type == 'out_invoice':
            res['invoice_payment_term_id'] = move.invoice_payment_term_id.id
        return res


class AccountMove(models.Model):
    _inherit = "account.move"

    gross_profit = fields.Monetary(compute='calculate_gross_profit', string='Predicted Profit')
    storage_down_payment = fields.Boolean(copy=False)
    # discount_from_batch = fields.Float('WriteOff Discount')
    invoice_address_id = fields.Many2one('res.partner', string="Billing Address")



    @api.model
    def create(self, vals):
        context = dict(self._context)
        context.update(tracking_disable=True)
        # if vals.get('move_type', '') != 'entry':
        self = self.with_context(context)
        return super(AccountMove, self).create(vals)

    def write(self, vals):
        context = dict(self._context)
        context.update(tracking_disable=True)
        self = self.with_context(context)
        return super(AccountMove, self).write(vals)


    @api.depends('invoice_line_ids.profit_margin')
    def calculate_gross_profit(self):
        """
         re implemented in batch delivery
        """
        pass

    def action_post(self):
        for move in self:
            if move.is_sale_document() and not move.invoice_payment_term_id and not move.rma_id:
                raise ValidationError('Payment term is not set for invoice %s' % move.name)
        return super().action_post()

    def is_storage_contract_move(self):
        self.ensure_one()
        if any(self.invoice_line_ids.mapped('is_storage_contract')) and any(self.invoice_line_ids.mapped('sale_line_ids').mapped('order_id.storage_contract')):
            return "storage_contract"
        return any(self.invoice_line_ids.mapped('is_storage_contract'))

    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
        """
        override to do teh anglo saxon changes for SC
        """
        processed = self.env[self._name]
        lines_vals_list = []
        for move in self:
            sc_state = move.is_storage_contract_move()
            if move.is_sale_document() and sc_state:
                processed |= move
                for line in move.invoice_line_ids:

                    # Filter out lines being not eligible for COGS.
                    if not line._eligible_for_cogs() and not line.is_storage_contract_candidate():
                        continue

                    # Retrieve accounts needed to generate the COGS.
                    accounts = line.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=move.fiscal_position_id)
                    debit_interim_account = accounts['sc_liability_out']


                    credit_expense_account = accounts['expense'] or move.journal_id.default_account_id
                    if sc_state == 'storage_contract':
                        # if it is storage order reverse the move lines
                        debit_interim_account = accounts['stock_output']
                        credit_expense_account = accounts['sc_liability_out']
                    if not debit_interim_account or not credit_expense_account:
                        continue

                    # Compute accounting fields.
                    sign = -1 if move.move_type == 'out_refund' else 1
                    price_unit = line._stock_account_get_anglo_saxon_price_unit()
                    balance = sign * line.quantity * price_unit

                    # Add interim account line.
                    lines_vals_list.append({
                        'name': line.name[:64],
                        'move_id': move.id,
                        'partner_id': move.commercial_partner_id.id,
                        'product_id': line.product_id.id,
                        'product_uom_id': line.product_uom_id.id,
                        'quantity': line.quantity,
                        'price_unit': price_unit,
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                        'account_id': debit_interim_account.id,
                        'exclude_from_invoice_tab': True,
                        'is_anglo_saxon_line': True,
                    })

                    # Add expense account line.
                    lines_vals_list.append({
                        'name': line.name[:64],
                        'move_id': move.id,
                        'partner_id': move.commercial_partner_id.id,
                        'product_id': line.product_id.id,
                        'product_uom_id': line.product_uom_id.id,
                        'quantity': line.quantity,
                        'price_unit': -price_unit,
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                        'account_id': credit_expense_account.id,
                        'analytic_account_id': line.analytic_account_id.id,
                        'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                        'exclude_from_invoice_tab': True,
                        'is_anglo_saxon_line': True,
                    })
        res = super(AccountMove, self)._stock_account_prepare_anglo_saxon_out_lines_vals()
        return lines_vals_list + res

    def button_cancel(self):
        for move in self:
            if move.is_sale_document():
                for sale_order in move.mapped('invoice_line_ids').mapped('sale_line_ids').mapped('order_id'):
                    if sale_order.storage_contract and sale_order.state == 'released':
                        sale_order.write({'state': 'done'})
        return super().button_cancel()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"


    profit_margin = fields.Monetary(compute='calculate_profit_margin', string="Profit Margin")
    lst_price = fields.Float(string='Standard Price', digits='Product Price', store=True, compute='_compute_lst_cost_prices')
    working_cost = fields.Float(string='Working Cost', digits='Product Price', store=True, compute='_compute_lst_cost_prices')
    is_storage_contract = fields.Boolean(compute='_compute_is_storage_contract', store=True)

    @api.depends('sale_line_ids.storage_contract_line_id', 'sale_line_ids.order_id.storage_contract')
    def _compute_is_storage_contract(self):
        for line in self:
            if line.sale_line_ids:
                if len(line.sale_line_ids.mapped('storage_contract_line_id.id')):
                    line.is_storage_contract = True
                elif any(line.sale_line_ids.mapped('order_id.storage_contract')):
                    line.is_storage_contract = True
                else:
                    line.is_storage_contract = False
            elif line.purchase_line_id and line.purchase_line_id.sale_line_id:
                if line.purchase_line_id.sale_line_id.storage_contract_line_id:
                    line.is_storage_contract = True
                elif line.purchase_line_id.sale_line_id.order_id.storage_contract:
                    line.is_storage_contract = True
                else:
                    line.is_storage_contract = False

    @api.depends('product_id', 'price_unit', 'quantity')
    def calculate_profit_margin(self):
        """
        Calculate profit margin in account invoice
        """
        for line in self:
            line.profit_margin = 0.0
            if not line.move_id.is_sale_document():
                continue
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

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.name
            self.product_uom_id = self.product_id.uom_id
            return {'domain': {'product_uom_id': [('id', 'in', self.product_id.sale_uoms.ids)]}}
        return {}

    @api.depends('product_id', 'product_uom_id')
    def _compute_lst_cost_prices(self):
        for line in self:
            if line.product_id and line.product_uom_id:
                uom_price = line.product_id.uom_standard_prices.filtered(lambda r: r.uom_id == line.product_uom_id)
                if len(uom_price) > 0:
                    uom_price = uom_price[0]
                    line.lst_price = uom_price.price
                    line.working_cost = uom_price.cost or 0

    def _get_computed_price_unit(self):
        res = super()._get_computed_price_unit()
        if self.move_id.is_sale_document():
            prices_all = self.env['customer.product.price']
            for rec in self.move_id.partner_id.customer_pricelist_ids:
                if not rec.pricelist_id.expiry_date or rec.pricelist_id.expiry_date >= str(date.today()):
                    prices_all |= rec.pricelist_id.customer_product_price_ids
            prices_all = prices_all.filtered(
                lambda r: r.product_id.id == self.product_id.id and r.product_uom.id == self.product_uom_id.id and (
                        not r.partner_id or r.partner_id.id == self.move_id.partner_id.id))
            product_price = 0.0
            for price_rec in prices_all:
                if not price_rec.partner_id and prices_all.filtered(lambda r: r.partner_id):
                    continue
                product_price = price_rec.price
                break
            if not product_price:
                if self.product_uom_id and self.product_id:
                    uom_price = self.product_id.uom_standard_prices.filtered(lambda r: r.uom_id == self.product_uom_id)
                    if uom_price:
                        product_price = uom_price[0].price
            if self.product_id.uom_id == self.product_uom_id and self.quantity % 1 != 0.0:
                product_price = ((int(self.quantity / 1) * product_price) + ((self.quantity % 1) * product_price * (
                        (100 + self.product_id.categ_id.repacking_upcharge) / 100))) / self.quantity
            res = product_price

            sale_tax_history = self.env['sale.tax.history'].search(
                [('partner_id', '=', self.move_id.partner_shipping_id.id), ('product_id', '=', self.product_id.id)], limit=1)
            if sale_tax_history and not sale_tax_history.tax:
                self.tax_ids = [(5, _, _)]

        return res

    def _get_computed_taxes(self):
        if self.move_id.is_sale_document():
            sale_tax_history = self.env['sale.tax.history'].search(
                [('partner_id', '=', self.move_id.partner_shipping_id.id), ('product_id', '=', self.product_id.id)],
                limit=1)
            if sale_tax_history and not sale_tax_history.tax:
                return self.env['account.tax']
        return super()._get_computed_taxes()

    def _eligible_for_cogs(self):

        self.ensure_one()
        if self.is_storage_contract and any(self.sale_line_ids.mapped('order_id.storage_contract')):
            return False
        if self.is_storage_contract:
            return False
        return super(AccountMoveLine, self)._eligible_for_cogs()

    def is_storage_contract_candidate(self):
        self.ensure_one()
        if self.is_storage_contract and any(self.sale_line_ids.mapped('order_id.storage_contract')):
            return True
        if self.is_storage_contract:
            return True


class PaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    set_to_default = fields.Boolean(string='Default')
    order_type = fields.Selection([('purchase', 'Purchase'), ('sale', 'Sale')], string='Type')
    code = fields.Char(string='Code')
    due_days = fields.Integer(string='Discount Days')
    discount_per = fields.Float(string='Discount Percent')
    is_discount = fields.Boolean('Is Cash Discount', help="Check this box if this payment term is \
        a cash discount. If cash discount is used the remaining amount of the invoice will not be paid")

    @api.onchange('is_discount')
    def onchange_is_discount(self):
        if self.is_discount is False:
            self.due_days = False
            self.discount_per = False

PaymentTerm()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
