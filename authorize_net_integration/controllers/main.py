# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import werkzeug.utils
import re


class PaymentPageWeb(http.Controller):

    def check_string(self, inp_string):
        op_string = ''
        if inp_string:
            op_string = inp_string.replace('&', 'and')  # replaces '&' with 'and'
            op_string = re.sub('<.+?>', ' ', op_string)  # removes any characters in between '<' and '>'
            op_string = re.sub('@.+', ' ', op_string)  # removes any character that comes after '@'
            op_string = re.sub('[^-_A-Za-z0-9]', ' ', op_string)  # replace all the special character except ,-_
        return op_string

    # For Sale order Payment
    @http.route(['/authorize/payment'], type='http', auth="public")
    def customer_confirmation(self, token, error=None):
        """
            redirect to the payment page

        """
        if token:
            payment_token = request.env['payment.token.invoice'].sudo().search(
                [('token', '=', token), ('model', '=', 'sale')])
            if payment_token:
                if payment_token.state == 'draft':
                    edi_record = request.env['payment.token.invoice'].sudo().get_authorization_document(token)
                    warning = False
                    # if error:
                    #     warning = request.env['error.box'].sudo().search([('order', '=', edi_record.invoice_id.number)],
                    #                                                      order='id DESC', limit=1)
                    #     warning = self.check_string(warning.error_message)
                    #     warning = warning.split('-')
                    #     if len(warning) > 1:
                    #         warning = warning and warning[1]
                    journal_rec = request.env['account.journal'].sudo().search([('is_authorizenet', '=', True)],
                                                                               limit=1)
                    surcharge_percentage = journal_rec and journal_rec.surcharge_customer or 0

                    residue = edi_record.order_id.amount_total - edi_record.order_id.down_payment_amount
                    handing_fee = (residue * surcharge_percentage) / 100

                    return request.render("authorize_net_integration.PaymentView", {
                        'total_amount': round(float(handing_fee + residue), 2),
                        'order_id': edi_record.order_id, 'invoice_id': edi_record.invoice_id, 'status': 'draft',
                        'warning': warning, 'handling_fee': round(float(handing_fee), 2)})

                # elif payment_token.payment_status in ('clear_production', 'clear_shipping'):
                #     return request.render("authorize_net_integration.PaymentResultView", {'status': 'already'})
                elif payment_token.invoice_id.state == 'paid':
                    return request.render("authorize_net_integration.PaymentResultView", {'status': 'invoice-paid'})
                else:
                    edi_record = request.env['payment.token.invoice'].sudo().get_authorization_document(token)
                    edi_record.state = 'expired'
                    return request.render("authorize_net_integration.PaymentResultView", {'status': edi_record.state})
            else:
                return request.render("authorize_net_integration.PaymentResultView", {'status': 'not_exist'})

        else:
            return request.render("authorize_net_integration.PaymentResultView", {'status': 'not_exist'})

    # For Sale order Payment Success
    @http.route(['/verification'], methods=['GET', 'POST'], type='http', auth="public")
    def customer_verification(self, **form):
        """
        details of card after submission
        authorization and capture payments
        """
        print('form', form)
        # invoice = form['name']
        order = form['order']
        total_amount = float(form['total'])
        handling_fee = 0
        if 'handling_fee' in form:
            handling_fee = float(form['handling_fee'])
        invoice_total = float(form['invoice_total'])
        sale_obj = request.env['sale.order'].sudo().search([('name', '=', order)])
        draft_invoice_ids = sale_obj.invoice_ids.filtered(
            lambda r: r.state not in ('paid', 'cancel') and r.type == 'out_invoice')
        print('draft_invoice_ids', draft_invoice_ids)
        inv_draft_amount = 0
        for draft_invoice in draft_invoice_ids:
            inv_draft_amount += draft_invoice.amount_total
        if sale_obj.invoice_status == 'invoiced' and inv_draft_amount >= sale_obj.amount_total:
            return request.render("authorize_net_integration.PaymentResultView", {'status': 'invoice-created'})

        paid_invoice_ids = sale_obj.invoice_ids.filtered(
            lambda r: r.state == 'paid' and r.type == 'out_invoice')
        print('paid_invoice_ids', paid_invoice_ids)
        inv_paid_amount = 0
        for paid_invoice in paid_invoice_ids:
            inv_paid_amount += paid_invoice.amount_total
        if sale_obj.invoice_status == 'invoiced' and inv_paid_amount >= sale_obj.amount_total:
            return request.render("authorize_net_integration.PaymentResultView", {'status': 'invoice-paid'})

        paid_amount = sale_obj.down_payment_amount
        invoice = sale_obj.sudo().create_down_payment(total_amount, handling_fee, invoice_total, paid_amount)
        print('invoice', invoice)
        payment_token = request.env['payment.token.invoice'].sudo().search(
            [('order_id.name', '=', order), ('model', '=', 'sale')])
        payment_token.invoice_id = invoice
        if payment_token.state not in ('paid', 'expired'):
            card = form['card']
            cvv = form['cvv']
            amount = form['total']
            expiry = form['month'] + form['year']
            surcharge = handling_fee
            # payment_token.invoice_id.write({'due_amount_gateway': payment_token.invoice_id.residual})
            transaction_id, error = sale_obj.sudo().get_aim_transaction(amount, card, cvv, expiry, invoice.id,
                                                                        surcharge=surcharge)
            print('', )
            if transaction_id:
                payment_token.write({'state': 'paid'})
                return request.render("authorize_net_integration.PaymentResultViewSuccess",
                                      {'status': payment_token.state, 'amount': float(amount),
                                       'type': form.get('selected_p_method', False), 'order_id': payment_token.order_id,
                                       'invoice_id': payment_token.invoice_id})
            elif error:
                return werkzeug.utils.redirect(
                    '/authorize/payment?token=%s&error=%s' % (payment_token.token, True))

        elif payment_token.invoice_id.state == 'paid':
            return request.render("authorize_net_integration.PaymentResultView", {'status': 'invoice-paid'})
        else:
            payment_token.state = 'expired'
            return request.render("authorize_net_integration.PaymentResultView", {'status': payment_token.state})

    # For Invoice Payment
    @http.route(['/authorize/payment/invoice'], type='http', auth="public")
    def customer_confirmation_invoice(self, token, error=None):
        """
            redirect to the payment page

        """
        edi_record = request.env['payment.token.invoice'].sudo().search(
            [('token', '=', token), ('model', '=', 'invoice')])
        invoice_ids = request.env['account.invoice'].sudo().search(
            [('partner_id', '=', edi_record.invoice_id.partner_id.id)])
        invoice_ids = invoice_ids.filtered(lambda r: r.state == 'open' and r.type == 'out_invoice')
        credit_memo = request.env['account.invoice'].sudo().search(
            [('partner_id', '=', edi_record.invoice_id.partner_id.id)])
        credit_memo = credit_memo.filtered(lambda r: r.state == 'open' and r.type == 'out_refund')
        if edi_record:
            edi_record.state = 'draft'
            warning = False
            if error:
                warning = request.env['error.box'].sudo().search([('order', '=', edi_record.invoice_id.number)],
                                                                 order='id DESC', limit=1)
                warning = self.check_string(warning.error_message)
                warning = warning.split("-")
                if len(warning) > 1:
                    warning = warning and warning[1]
            if edi_record.invoice_id.state == 'paid':
                return request.render("authorize_net_integration.PaymentResultView", {'status': 'invoice-paid'})
            elif edi_record.invoice_id.state != 'open':
                return request.render("authorize_net_integration.PaymentResultView", {'status': 'not_exist'})
            invoice_ids = sorted(invoice_ids, key=lambda a: a.date_due)
            journal_rec = request.env['account.journal'].sudo().search([('is_authorizenet', '=', True)], limit=1)
            surcharge_percentage = journal_rec and journal_rec.surcharge_customer or 0
            handing_fee = (edi_record.invoice_id.residual * surcharge_percentage) / 100
            return request.render("authorize_net_integration.InvoicePaymentView",
                                  {'invoice_ids': invoice_ids, 'cm': credit_memo, 'invoice_id': edi_record.invoice_id,
                                   'surcharge_percentage': surcharge_percentage, 'warning': warning,
                                   'edi_record': edi_record, 'handling_fee': handing_fee})
        else:
            return request.render("authorize_net_integration.PaymentResultView", {'status': 'not_exist'})

    # For Invoice Payment Success
    @http.route(['/verification/invoice'], methods=['GET', 'POST'], type='http', auth="public")
    def customer_verification_invoice(self, **form):
        """
        details of card after submission
        authorization and capture payments
        """
        invoice_id = form['invoice_number']
        edi_record = request.env['payment.token.invoice'].sudo().search(
            [('invoice_id', '=', int(invoice_id)), ('model', '=', 'invoice')], limit=1)
        invoice_sudo = request.env['account.invoice'].sudo().browse(int(invoice_id))
        print('invoice_sudo.state', invoice_sudo.state)
        if invoice_sudo.state != 'open':
            return request.render("authorize_net_integration.PaymentResultView", {'status': 'invoice-paid'})
        if edi_record.state != 'submitted':
            extra = form['extra_amount']
            message = False
            if extra:
                extra = float(extra)
                message = form['message']
            else:
                extra = 0.0
            invoice_list = []
            amount = form['amount']
            card = form['card']
            cvv = form['cvv']
            expiry = form['month'] + form['year']
            inv_count = form.get('inv_count', 0)
            credit_count = form.get('credit_count', 0)
            for inv in range(int(inv_count)):
                invoice = form.get('invoice_box_' + str(inv))
                if invoice:
                    invoice_list.append(int(invoice))
            if credit_count:
                for inv in range(int(credit_count)):
                    invoice = form.get('credit_box_' + str(inv))
                    if invoice:
                        invoice_list.append(int(invoice))
            for inv in invoice_list:
                invoice_sudo = request.env['account.invoice'].sudo().browse(int(inv))
                invoice_sudo.write({'due_amount_gateway': invoice_sudo.due_amount_gateway + float(amount)})
            # invoice_sudo = request.env['account.invoice'].sudo().browse(int(invoice_id))
            # invoice_sudo.write({'due_amount_gateway': invoice_sudo.due_amount_gateway + invoice_sudo.residual})
            surcharge = 0
            if 'handling_fee' in form:
                surcharge = form['handling_fee']
            transaction_id, error = request.env['account.invoice'].sudo().aim_transaction_invoice(invoice_list, amount,
                                                                                                  card, cvv, expiry,
                                                                                                  extra, invoice_id,
                                                                                                  message,
                                                                                                  surcharge=float(
                                                                                                      surcharge))

            if transaction_id:
                edi_record.write({'state': 'submitted'})
                invoices = []
                for inv in invoice_list:
                    invoices.append(request.env['account.invoice'].sudo().browse(inv))
                return request.render("authorize_net_integration.InvoiceResultViewSuccess",
                                      {'invoice_ids': invoices, 'type': form.get('selected_p_method', False),
                                       'extra': extra, 'amount': amount, 'message': message})
            elif error:
                edi_record.write({'state': 'error'})
                return werkzeug.utils.redirect(
                    '/authorize/payment/invoice?token=%s&error=%s' % (edi_record.token, True))
        elif edi_record.invoice_id.state == 'paid':
            return request.render("authorize_net_integration.PaymentResultView", {'status': 'already'})
        else:
            edi_record.state = 'expired'
            return request.render("authorize_net_integration.PaymentResultView", {'status': edi_record.state})
