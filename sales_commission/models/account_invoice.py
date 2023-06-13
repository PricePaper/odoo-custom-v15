# -*- coding: utf-8 -*-

from datetime import datetime, date

from dateutil.relativedelta import relativedelta
from odoo.tools import float_round

from odoo import fields, models, api, _
from odoo.exceptions import UserError
import math


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    sales_person_ids = fields.Many2many('res.partner', string='Associated Sales Persons')
    check_bounce_invoice = fields.Boolean(string='Check Bounce Invoice', default=False)
    sale_commission_ids = fields.One2many('sale.commission', 'invoice_id', string='Commission')
    paid_date = fields.Date(string='Paid_date', compute='_compute_paid_date')
    commission_rule_ids = fields.Many2many('commission.rules', string='Commission Rules')

    def commission_correction(self):

        commission_vals={}
        to_date = "20220731"
        to_date = datetime.strptime(to_date, "%Y%m%d").date()
        invoices = self.env['account.move'].search([('payment_state', 'in', ('in_payment', 'paid')),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('check_bounce_invoice', '=', False)])
        from_date = "20220301"
        from_date = datetime.strptime(from_date, "%Y%m%d").date()
        invoices = invoices.filtered(lambda r: r.paid_date and r.paid_date >= from_date and r.paid_date <= to_date)
        print(len(invoices), 'lllllllllll')
        for invoice in invoices:
            for rec in invoice.commission_rule_ids:
                commission = 0
                profit = invoice.gross_profit
                if rec.based_on in ['profit', 'profit_delivery']:
                    if profit <= 0:
                        continue
                    commission = profit * (rec.percentage / 100)
                elif rec.based_on == 'invoice':
                    amount = invoice.amount_total
                    commission = amount * (rec.percentage / 100)
                if commission == 0:
                    continue
                type = 'Invoice'
                if invoice.move_type == 'out_refund':
                    commission = -commission
                    type = 'Refund'


                sale = invoice.invoice_line_ids.mapped('sale_line_ids').mapped('order_id')
                vals = {
                    'sale_person_id': rec.sales_person_id,
                    'sale_id': sale and sale,
                    'commission': commission,
                    'invoice_id': invoice,
                    'invoice_type': type,
                    'is_paid': True,
                    'invoice_amount': invoice.amount_total,
                    'commission_date': invoice.invoice_date and invoice.paid_date
                }



                if commission_vals.get(rec.sales_person_id):
                    if commission_vals.get(rec.sales_person_id).get(invoice.partner_id):
                        if commission_vals.get(rec.sales_person_id).get(invoice.partner_id).get(invoice):
                            commission_vals[rec.sales_person_id][invoice.partner_id][invoice].append(vals)
                        else:
                            commission_vals[rec.sales_person_id][invoice.partner_id][invoice] = [vals]
                    else:
                        commission_vals[rec.sales_person_id][invoice.partner_id] = {invoice : [vals]}
                else:
                    commission_vals[rec.sales_person_id] = {invoice.partner_id: {invoice : [vals]}}

                if invoice.move_type != 'out_refund' and invoice.paid_date > invoice.invoice_date_due:
                    extra_days = invoice.paid_date - invoice.invoice_date_due
                    if self.env.user.company_id.commission_ageing_ids:
                        commission_ageing = self.env.user.company_id.commission_ageing_ids.filtered(
                            lambda r: r.delay_days <= extra_days.days)
                        commission_ageing = commission_ageing.sorted(key=lambda r: r.delay_days, reverse=True)
                        if commission_ageing and commission_ageing[0].reduce_percentage:
                            commission = commission_ageing[0].reduce_percentage * commission / 100
                            vals = {
                                'sale_person_id': rec.sales_person_id,
                                'sale_id': sale,
                                'commission': -commission,
                                'invoice_id': invoice,
                                'invoice_type': 'Commission Aging',
                                'is_paid': True,
                                'invoice_amount': invoice.amount_total,
                                'commission_date': invoice.paid_date
                            }
                            if commission_vals.get(rec.sales_person_id):
                                if commission_vals.get(rec.sales_person_id).get(invoice.partner_id):
                                    if commission_vals.get(rec.sales_person_id).get(invoice.partner_id).get(invoice):
                                        commission_vals[rec.sales_person_id][invoice.partner_id][invoice].append(vals)
                                    else:
                                        commission_vals[rec.sales_person_id][invoice.partner_id][invoice] = [vals]
                                else:
                                    commission_vals[rec.sales_person_id][invoice.partner_id] = {invoice : [vals]}
                            else:
                                commission_vals[rec.sales_person_id] = {invoice.partner_id: {invoice : [vals]}}
        commission_diff = {}
        print(len(commission_vals), 'gggggggggggg')
        for rep,partners in commission_vals.items():
            for partner,invoices in partners.items():
                for invoice, vals_list in invoices.items():
                    commission = 0
                    for vals in vals_list:
                        commission += vals.get('commission')
                    old_commission_lines = invoice.mapped('sale_commission_ids').filtered(lambda r: r.sale_person_id == rep and r.is_paid)
                    old_commission = old_commission_lines and sum(old_commission_lines.mapped('commission')) or 0

                    if float_round(commission, precision_digits=2) != float_round(old_commission, precision_digits=2):
                        if math.isclose(commission, old_commission, abs_tol=0.1):
                            continue
                        vals1={'old_commission' : float_round(old_commission, precision_digits=2),
                              'commission_audit': float_round(commission, precision_digits=2)}
                        if commission_diff.get(rep):
                            if commission_diff.get(rep).get(partner):
                                if commission_diff.get(rep).get(partner).get(invoice):
                                    commission_diff[rep][partner][invoice].append(vals1)
                                else:
                                    commission_diff[rep][partner][invoice] = [vals1]
                            else:
                                commission_diff[rep][partner] = {invoice : [vals1]}
                        else:
                            commission_diff[rep] = {partner: {invoice : [vals1]}}

        for rep,partners in commission_diff.items():
            sum1 = 0
            sum2 = 0
            for partner,invoices in partners.items():
                for invoice, commission_d in invoices.items():
                    old_commission_lines = invoice.mapped('sale_commission_ids').filtered(lambda r: r.sale_person_id == rep and not r.is_paid)
                    if old_commission_lines:
                        old_commission_lines.unlink()

                    sale = invoice.invoice_line_ids.mapped('sale_line_ids').mapped('order_id')
                    if sale:
                        sale = sale[0].id
                    else:
                        sale = False
                    comm_corr = float_round(commission_d[0]['commission_audit'] - commission_d[0]['old_commission'], 2)

                    vals = {
                        'sale_person_id': rep.id,
                        'sale_id': sale,
                        'commission': comm_corr,
                        'invoice_id': invoice.id,
                        'invoice_type': invoice.move_type,
                        'invoice_amount': invoice.amount_total,
                        'commission_date':invoice.invoice_date,
                        'paid_date': invoice.paid_date and invoice.paid_date,
                        'is_paid': True
                    }
                    self.env['sale.commission'].create(vals)

                    sum1+=commission_d[0]['old_commission']
                    sum2+=commission_d[0]['commission_audit']
            print(rep.name, float_round(sum1, 2), float_round(sum2, 2), float_round(sum2-sum1, 2))
        return True


    def _compute_paid_date(self):
        for rec in self:
            paid_date = False
            if rec.move_type in ('out_invoice', 'out_refund') and rec.payment_state in ('in_payment', 'paid'):
                reconciled_lines = rec.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
                reconciled_amls = reconciled_lines.mapped('matched_debit_ids.debit_move_id') + \
                                  reconciled_lines.mapped('matched_credit_ids.credit_move_id')
                paid_date_list = reconciled_amls.mapped('date')
                if paid_date_list:
                    paid_date = max(paid_date_list)
            rec.paid_date = paid_date

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super(AccountInvoice, self)._onchange_partner_id()
        if self.partner_id and self.partner_id.sales_person_ids:
            if self.move_type in ['out_invoice', 'out_refund']:
                self.sales_person_ids = self.partner_id.sales_person_ids
            else:
                self.sales_person_ids = False
        else:
            self.sales_person_ids = False
        return res

    @api.onchange('sales_person_ids','partner_id')
    def onchange_sales_person_ids(self):
        if self.sales_person_ids:
            rules = self.partner_id.mapped('commission_percentage_ids').filtered(lambda r:r.sale_person_id in self.sales_person_ids).mapped('rule_id')
            if rules:
                sale_rep = rules.mapped('sales_person_id')
                non_sale_rep = self.sales_person_ids - sale_rep
                for rep in non_sale_rep:
                    rules |= rep.default_commission_rule
            else:
                for rep in self.sales_person_ids:
                    rules |= rep.mapped('default_commission_rule')
            self.commission_rule_ids = rules
        else:
            self.commission_rule_ids = False


    def _post(self, soft=True):
        res = super(AccountInvoice, self)._post(soft)
        for move in self:
            if move.check_bounce_invoice:
                continue
            rec = move.sudo().calculate_commission()
            if rec and move.move_type == 'out_refund' and move.amount_total == 0:
                rec.sudo().write({'is_paid': True, 'paid_date': date.today()})
            # if rec and move.move_type == 'out_invoice' and move.amount_total == 0:
            #     rec.sudo().write({'is_paid': True, 'paid_date': date.today()})
        return res

    def check_commission(self, lines):
        for line in lines:
            profit = self.gross_profit
            commission = line.commission
            payment_date = self.paid_date
            rule_id = self.commission_rule_ids.filtered(
                lambda r: r.sales_person_id == line.sale_person_id)
            if rule_id:
                if rule_id.based_on in ['profit', 'profit_delivery']:
                    # if profit <= 0 or (self.move_type == 'out_refund' and self.amount_total == 0):
                    if profit <= 0 or self.amount_total == 0:
                        line.write({'commission': 0})
                        continue
                    commission = profit * (rule_id.percentage / 100)
                elif rule_id.based_on == 'invoice':
                    amount = self.amount_total
                    commission = amount * (rule_id.percentage / 100)
                if self.move_type == 'out_refund':
                    commission = -float_round(commission, 2)
            line.write({'commission': commission})
            if self._context.get('is_cancelled') and commission < 0:
                line.is_cancelled = True

    def check_due_date(self, lines):
        """
        Apply commission Ageing by checking due date
        """

        for line in lines:
            payment_date = False
            reconciled_lines = self.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
            reconciled_amls = reconciled_lines.mapped('matched_debit_ids.debit_move_id') + \
                              reconciled_lines.mapped('matched_credit_ids.credit_move_id')
            paid_date_list = reconciled_amls.mapped('date')
            if paid_date_list:
                payment_date = max(paid_date_list)
            if payment_date and payment_date > self.invoice_date_due:
                extra_days = payment_date - self.invoice_date_due
                if self.env.user.company_id.commission_ageing_ids:
                    commission_ageing = self.env.user.company_id.commission_ageing_ids.filtered(
                        lambda r: r.delay_days <= extra_days.days)
                    commission_ageing = commission_ageing.sorted(key=lambda r: r.delay_days, reverse=True)
                    if commission_ageing and commission_ageing[0].reduce_percentage:
                        commission = commission_ageing[0].reduce_percentage * line.commission / 100
                        vals = {
                            'sale_person_id': line.sale_person_id.id,
                            'sale_id': line.sale_id and line.sale_id.id,
                            'commission': -commission,
                            'invoice_id': self.id,
                            'invoice_type': 'aging',
                            'is_paid': True,
                            'invoice_amount': self.amount_total,
                            'commission_date': self.invoice_date and self.invoice_date
                        }
                        commission_rec = self.env['sale.commission'].create(vals)


    def calculate_commission(self):

        if len(self.invoice_line_ids) == 1 and self.invoice_line_ids[0].quantity < 0:
            return False
        commission_rec = self.env['sale.commission'].search([('invoice_id', '=', self.id), ('is_paid', '=', False)])

        if not commission_rec and self.move_type in ['out_invoice', 'out_refund']:
            profit = self.gross_profit
            commission_rule = self.commission_rule_ids
            for rec in commission_rule:
                commission = 0
                if rec.based_on in ['profit', 'profit_delivery']:
                    commission = profit * (rec.percentage / 100)
                    # if profit <= 0 or (self.move_type == 'out_refund' and self.amount_total == 0):
                    if profit <= 0 or self.amount_total == 0:
                        commission = 0
                elif rec.based_on == 'invoice':
                    amount = self.amount_total
                    commission = amount * (rec.percentage / 100)
                if commission == 0:
                    continue
                if self.move_type == 'out_refund':
                    commission = -commission
                sale = self.invoice_line_ids.mapped('sale_line_ids')
                vals = {
                    'sale_person_id': rec.sales_person_id.id,
                    'sale_id': sale[-1].order_id.id if sale else False,
                    'commission': commission,
                    'invoice_id': self.id,
                    'invoice_type': self.move_type,
                    'is_paid': False,
                    'invoice_amount': self.amount_total,
                    'commission_date': self.invoice_date and self.invoice_date
                }
                commission_rec |= self.env['sale.commission'].create(vals)
        return commission_rec

    def js_remove_outstanding_partial(self, partial_id):
        partial = self.env['account.partial.reconcile'].browse(partial_id)
        moves = partial.debit_move_id.move_id + partial.credit_move_id.move_id - self
        moves = moves.filtered(lambda r: r.move_type in ('out_refund', 'out_invoice'))
        for move in moves:
            commission_rec = self.env['sale.commission'].search([('invoice_id', '=', move.id)])
            settled_rec = commission_rec.filtered(
                lambda r: r.is_settled and r.invoice_type != 'unreconcile' and not r.is_cancelled)
            for rec in settled_rec:
                commission = rec.commission
                vals = {
                    'sale_person_id': rec.sale_person_id.id,
                    'commission': -commission,
                    'invoice_id': move.id,
                    'invoice_type': 'unreconcile',
                    'is_paid': True,
                    'invoice_amount': move.amount_total,
                    'commission_date': date.today(),
                    'paid_date': date.today(),
                }
                self.env['sale.commission'].create(vals)
                rec.is_cancelled = True

            paid_rec = commission_rec.filtered(lambda r: not r.is_settled and r.invoice_type != 'unreconcile')
            paid_rec and paid_rec.unlink()
        res = super().js_remove_outstanding_partial(partial_id)
        return res


    def button_cancel(self):
        for invoice in self:
            commission_rec = self.env['sale.commission'].search([('invoice_id', '=', invoice.id)])
            settled_rec = commission_rec.filtered(
                lambda r: r.is_settled and not r.is_cancelled and r.invoice_type != 'cancel')
            for rec in settled_rec:
                commission = rec.commission
                vals = {
                    'sale_person_id': rec.sale_person_id.id,
                    'commission': -commission,
                    'invoice_id': invoice.id,
                    'invoice_type': 'cancel',
                    'is_paid': True,
                    'invoice_amount': self.amount_total,
                    'commission_date': date.today(),
                    'paid_date': date.today(),
                }
                self.env['sale.commission'].create(vals)
                rec.is_cancelled = True

            paid_rec = commission_rec.filtered(lambda r: not r.is_settled and r.invoice_type != 'cancel')
            paid_rec and paid_rec.unlink()
        res = super(AccountInvoice, self).button_cancel()
        return res

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def reconcile(self):

        moves = self.mapped('move_id')
        invs = moves.filtered(lambda r: r.move_type in ('out_refund', 'out_invoice'))
        pay_state = {}
        for inv in invs:
            pay_state[inv] = inv.payment_state
        res = super(AccountMoveLine, self).reconcile()

        invoices = moves.filtered(lambda r: r.move_type in ('out_refund', 'out_invoice') and r.payment_state in ('in_payment', 'paid'))
        for invoice in invoices:
            if invoice.check_bounce_invoice:
                continue
            if invoice in pay_state and pay_state[invoice] == 'in_payment' and invoice.payment_state == 'paid':
                continue
            rec = invoice.sudo().calculate_commission()
            rec.sudo().write({'is_paid': True})
            invoice.sudo().check_commission(rec)
            if invoice.move_type != 'out_refund':
                invoice.sudo().check_due_date(rec)
        return res


    def remove_move_reconcile(self):
        partial = self.matched_debit_ids + self.matched_credit_ids
        moves = partial.mapped('debit_move_id').mapped('move_id') + partial.mapped('credit_move_id').mapped('move_id')
        moves = moves.filtered(lambda r: r.move_type in ('out_refund', 'out_invoice'))
        for move in moves:
            commission_rec = self.env['sale.commission'].search([('invoice_id', '=', move.id)])
            settled_rec = commission_rec.filtered(
                lambda r: r.is_settled and r.invoice_type != 'unreconcile' and not r.is_cancelled)
            for rec in settled_rec:
                commission = rec.commission
                vals = {
                    'sale_person_id': rec.sale_person_id.id,
                    'commission': -commission,
                    'invoice_id': move.id,
                    'invoice_type': 'unreconcile',
                    'is_paid': True,
                    'invoice_amount': move.amount_total,
                    'commission_date': date.today(),
                    'paid_date': date.today(),
                }
                self.env['sale.commission'].create(vals)
                rec.is_cancelled = True

            paid_rec = commission_rec.filtered(lambda r: not r.is_settled and r.invoice_type != 'unreconcile')
            paid_rec and paid_rec.unlink()
        res = super(AccountMoveLine, self).remove_move_reconcile()
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
