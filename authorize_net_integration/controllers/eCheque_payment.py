# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import werkzeug.utils


class PaymentPageCheque(http.Controller):

    @http.route(['/eCheque_payment'], methods=['GET', 'POST'], type='http', auth="public")
    def cheque_payment(self, **form):
        """
            submit the cheque payment form

        """
        print('form', form)
        account_name = form.get('account_name', False)
        routing_number = form.get('routing_number', False)
        account_number = form.get('account_number', False)
        bank_name = form.get('bank_name', False)
        eCheque_type = 'WEB'
        account_type = 'savings'
        surcharge = form.get('handling_fee', False)
        amount = form.get('total', False)
        invoice = form.get('name', False)

        if 'order' in form:
            order = form.get('order', False)
            total_amount = float(form.get('total', False))
            invoice_total = float(form.get('invoice_total', False))
            handling_fee = 0
            if 'handling_fee' in form:
                handling_fee = float(form['handling_fee'])
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

            # if sale_obj.invoice_status != 'to invoice':
            #     return request.render("authorize_net_integration.PaymentResultView", {'status': 'invoice-paid'})
            paid_amount = sale_obj.down_payment_amount
            print('paramsssssssssss', total_amount, handling_fee, invoice_total, paid_amount)
            invoice = sale_obj.sudo().create_down_payment(total_amount, handling_fee, invoice_total, paid_amount)
            print('invoice', invoice)
            if invoice.state == 'paid':
                return request.render("authorize_net_integration.PaymentResultView", {'status': 'invoice-paid'})
            payment_token = request.env['payment.token.invoice'].sudo().search(
                [('order_id.name', '=', order), ('model', '=', 'sale')])
            payment_token.invoice_id = invoice
            invoice = invoice.id

        invoice_id = form.get('invoice_number', False)
        payment_token = request.env['payment.token.invoice'].sudo().search(
            [('invoice_id.id', '=', invoice), ('model', '=', 'sale')])
        inv_count = form.get('inv_count', 0)
        credit_count = form.get('credit_count', 0)
        invoice_list = []
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
            if invoice_sudo.state in ('paid', 'cancel'):
                return request.render("authorize_net_integration.PaymentResultView", {'status': 'invoice-paid'})
            invoice_sudo.write({'due_amount_gateway': invoice_sudo.due_amount_gateway + float(amount)})
        edi_record = request.env['payment.token.invoice'].sudo().search(
            [('invoice_id', '=', invoice_id and int(invoice_id)), ('model', '=', 'invoice')], limit=1)
        # call from sales preproduction or shipping
        if payment_token and not invoice_list:
            if sale_obj and payment_token and payment_token.state not in (
                    'paid', 'expired'):
                # payment_token.invoice_id.write({'due_amount_gateway': payment_token.invoice_id.residual})
                transaction_id, error = sale_obj.sudo().get_aim_transaction(amount=round(float(amount), 2),
                                                                            invoice=invoice,
                                                                            account_name=account_name,
                                                                            routing_number=routing_number, \
                                                                            account_number=account_number,
                                                                            bank_name=bank_name, \
                                                                            eCheque_type=eCheque_type,
                                                                            account_type=account_type,
                                                                            surcharge=surcharge)
                if transaction_id:
                    payment_token.write({'state': 'paid'})
                    return request.render("authorize_net_integration.PaymentResultViewSuccess",
                                          {'status': payment_token.state, 'type': form.get('selected_p_method', False),
                                           'amount': float(amount),
                                           'order_id': payment_token.order_id, 'invoice_id': payment_token.invoice_id})
                elif error:
                    return werkzeug.utils.redirect(
                        '/authorize/payment?token=%s&error=%s' % (payment_token.token, True))

            elif payment_token.invoice_id.state == 'paid':
                return request.render("authorize_net_integration.PaymentResultView", {'status': 'invoice-paid'})
            else:
                payment_token.state = 'expired'
                return request.render("authorize_net_integration.PaymentResultView", {'status': payment_token.state})
        # call from multi select invoice payment view
        elif invoice_list and edi_record and edi_record.state != 'submitted':
            extra = form.get('extra_amount', 0.0)
            message = form.get('message', False)
            amount = form.get('amount', False)
            if extra:
                extra = float(extra)
            transaction_id, error = request.env['account.invoice'].sudo().aim_transaction_invoice(
                invoice_list=invoice_list, amount=round(float(amount), 2), invoice=invoice_id,
                account_name=account_name, routing_number=routing_number, \
                account_number=account_number, bank_name=bank_name, \
                eCheque_type=eCheque_type, account_type=account_type, extra=extra, message=message,
                surcharge=surcharge)
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
        elif edi_record and edi_record.invoice_id.state == 'paid':
            return request.render("authorize_net_integration.PaymentResultView", {'status': 'already'})
        else:
            edi_record.state = 'expired'
            return request.render("authorize_net_integration.PaymentResultView", {'status': edi_record.state})
