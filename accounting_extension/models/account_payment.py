# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang, format_date

INV_LINES_PER_STUB = 9


class AccountRegisterPayment(models.TransientModel):
    _inherit = "account.payment.register"

    def _post_payments(self, to_process, edit_mode=False):
        """
        override to post discount move if exist
        """
        res = super()._post_payments(to_process, edit_mode)
        if edit_mode:
            for vals in to_process:
                payment = vals['payment']
                if payment.discount_move_id:
                    payment.discount_move_id.action_post()
        return res

    def _reconcile_payments(self, to_process, edit_mode=False):
        """
        reconcile the discount move
        """
        res = super()._reconcile_payments(to_process, edit_mode)
        if edit_mode:
            vals = to_process[0]
            payment = vals.get('payment')
            if payment.partner_type == 'customer' and payment.discount_move_id:
                discount_limit = self.env['ir.config_parameter'].sudo().get_param('accounting_extension.customer_discount_limit', 5.00)
                if isinstance(discount_limit, str):
                    discount_limit = float(discount_limit)
                discount_limit = sum(payment.reconciled_invoice_ids.mapped('amount_total')) * (discount_limit / 100)
                if payment.discount_move_id.amount_total > discount_limit:
                    raise UserError('Invoices can not be discounted more than $ %.2f.\nCreate a credit memo instead.' % discount_limit)
                counterpart_line = vals.get('to_reconcile')
                counterpart_line |= payment.discount_move_id.line_ids.filtered(lambda r: r.account_id.user_type_id.type in ('receivable', 'payable'))
                counterpart_line.reconcile()
        return res

    def _init_payments(self, to_process, edit_mode=False):
        """
        create discount move from write of vals
        seperating it from payment journal
        to keep the uniqueness
        """
        write_off_vals = False
        if edit_mode:
            for vals in to_process:
                write_off_vals = vals['create_vals'].pop('write_off_line_vals', False)
        payments = super()._init_payments(to_process, edit_mode)
        if write_off_vals:
            destination_account_id = payments.partner_id and payments.partner_id.property_account_receivable_id or self.env['ir.property']._get(
                'property_account_receivable_id', 'res.partner')
            if payments.partner_type == 'supplier':
                destination_account_id = payments.partner_id and payments.partner_id.property_account_payable_id or self.env['ir.property']._get(
                    'property_account_payable_id', 'res.partner')
            discount_move = self.env['account.move'].create({
                'move_type': 'entry',
                'company_id': payments.company_id.id,
                'date': fields.Date.today(),
                'journal_id': payments.journal_id.id,
                'ref': '%s - Discount' % payments.ref,
                'line_ids': [(0, 0, {
                    'account_id': destination_account_id.id,
                    'company_currency_id': payments.company_id.currency_id.id,
                    'credit': 0.0 if payments.partner_type == 'supplier' else write_off_vals.get('amount', 0),
                    'debit': write_off_vals.get('amount', 0) if payments.partner_type == 'supplier' else 0.0,
                    'journal_id': payments.journal_id.id,
                    'name': write_off_vals.get('name'),
                    'partner_id': payments.partner_id.id
                }), (0, 0, {
                    'account_id': write_off_vals.get('account_id'),
                    'company_currency_id': payments.company_id.currency_id.id,
                    'credit': write_off_vals.get('amount', 0) if payments.partner_type == 'supplier' else 0.0,
                    'debit': 0.0 if payments.partner_type == 'supplier' else write_off_vals.get('amount', 0),
                    'journal_id': payments.journal_id.id,
                    'name': write_off_vals.get('name'),
                    'partner_id': payments.partner_id.id
                })]
            })
            payments.write({'discount_move_id': discount_move.id})
        return payments


AccountRegisterPayment()


class AccountPayment(models.Model):
    _inherit = "account.payment"

    discount_move_id = fields.Many2one('account.move', 'Discount Move')

    def warapper_compute_reconciliation_status(self):
        for pay in self:
            pay._compute_reconciliation_status()
        return True

            
    @api.depends('move_id.line_ids.amount_residual', 'move_id.line_ids.amount_residual_currency', 'move_id.line_ids.account_id')
    def _compute_reconciliation_status(self):
        """
        Override to fix cash account automatic matching

        """
        cash_payments = self.filtered(lambda rec: rec.journal_id.default_account_id.reconcile)
        for pay in cash_payments:
            liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()
            if not pay.currency_id or not pay.id:
                pay.is_reconciled = False
                pay.is_matched = False
            elif pay.currency_id.is_zero(pay.amount):
                pay.is_reconciled = True
                pay.is_matched = True
            else:
                residual_field = 'amount_residual' if pay.currency_id == pay.company_id.currency_id else 'amount_residual_currency'
                pay.is_matched = pay.currency_id.is_zero(sum(liquidity_lines.mapped(residual_field)))

                reconcile_lines = (counterpart_lines + writeoff_lines).filtered(lambda line: line.account_id.reconcile)
                pay.is_reconciled = pay.currency_id.is_zero(sum(reconcile_lines.mapped(residual_field)))
        return super(AccountPayment, self - cash_payments)._compute_reconciliation_status()

    def _check_build_page_info(self, i, p):
        result = super(AccountPayment, self)._check_build_page_info(i, p)
        result.update({'have_bills': self.payment_type == 'outbound'})
        return result

    def _check_make_stub_pages(self):
        """ The stub is the summary of paid invoices. It may spill on several pages, in which case only the check on
            first page is valid. This function returns a list of stub lines per page.
        """
        self.ensure_one()

        def prepare_vals(invoice, partials):
            number = ' - '.join([invoice.name, invoice.ref] if invoice.ref else [invoice.name])

            if invoice.is_outbound():
                invoice_sign = 1
                partial_field = 'debit_amount_currency'
            else:
                invoice_sign = -1
                partial_field = 'credit_amount_currency'

            if invoice.currency_id.is_zero(invoice.amount_residual):
                amount_residual_str = '-'
            else:
                amount_residual_str = formatLang(self.env, invoice_sign * invoice.amount_residual, currency_obj=invoice.currency_id)

            result =  {
                'due_date': format_date(self.env, invoice.invoice_date_due),
                'number': number,
                'amount_total': formatLang(self.env, invoice_sign * invoice.amount_total, currency_obj=invoice.currency_id),
                'amount_residual': amount_residual_str,
                'amount_paid': formatLang(self.env, invoice_sign * sum(partials.mapped(partial_field)), currency_obj=self.currency_id),
                'currency': invoice.currency_id,
            }
            discount = invoice.get_discount()
            result.update({'discount': formatLang(self.env, discount, currency_obj=invoice.currency_id)})
            return result

        # Decode the reconciliation to keep only invoices.
        term_lines = self.line_ids.filtered(lambda line: line.account_id.internal_type in ('receivable', 'payable'))
        invoices = (term_lines.matched_debit_ids.debit_move_id.move_id + term_lines.matched_credit_ids.credit_move_id.move_id)\
            .filtered(lambda x: x.is_outbound())
        invoices = invoices.sorted(lambda x: x.invoice_date_due or x.date)

        # Group partials by invoices.
        invoice_map = {invoice: self.env['account.partial.reconcile'] for invoice in invoices}
        for partial in term_lines.matched_debit_ids:
            invoice = partial.debit_move_id.move_id
            if invoice in invoice_map:
                invoice_map[invoice] |= partial
        for partial in term_lines.matched_credit_ids:
            invoice = partial.credit_move_id.move_id
            if invoice in invoice_map:
                invoice_map[invoice] |= partial

        # Prepare stub_lines.
        if 'out_refund' in invoices.mapped('move_type'):
            stub_lines = [{'header': True, 'name': "Bills"}]
            stub_lines += [prepare_vals(invoice, partials)
                           for invoice, partials in invoice_map.items()
                           if invoice.move_type == 'in_invoice']
            stub_lines += [{'header': True, 'name': "Refunds"}]
            stub_lines += [prepare_vals(invoice, partials)
                           for invoice, partials in invoice_map.items()
                           if invoice.move_type == 'out_refund']
        else:
            stub_lines = [prepare_vals(invoice, partials)
                          for invoice, partials in invoice_map.items()
                          if invoice.move_type == 'in_invoice']

        # Crop the stub lines or split them on multiple pages
        if not self.company_id.account_check_printing_multi_stub:
            # If we need to crop the stub, leave place for an ellipsis line
            num_stub_lines = len(stub_lines) > INV_LINES_PER_STUB and INV_LINES_PER_STUB - 1 or INV_LINES_PER_STUB
            stub_pages = [stub_lines[:num_stub_lines]]
        else:
            stub_pages = []
            i = 0
            while i < len(stub_lines):
                # Make sure we don't start the credit section at the end of a page
                if len(stub_lines) >= i + INV_LINES_PER_STUB and stub_lines[i + INV_LINES_PER_STUB - 1].get('header'):
                    num_stub_lines = INV_LINES_PER_STUB - 1 or INV_LINES_PER_STUB
                else:
                    num_stub_lines = INV_LINES_PER_STUB
                stub_pages.append(stub_lines[i:i + num_stub_lines])
                i += num_stub_lines

        return stub_pages

    def _synchronize_from_moves(self, changed_fields):
        self = self - self.filtered(lambda rec: rec.date < self.company_id._get_user_fiscal_lock_date())
        return super(AccountPayment, self)._synchronize_from_moves(changed_fields)



AccountPayment()
