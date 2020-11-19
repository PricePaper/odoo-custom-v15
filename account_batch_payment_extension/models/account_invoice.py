# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date
from odoo.exceptions import UserError



class Accountinvoice(models.Model):
    _inherit = "account.invoice"

    check_bounce_invoice = fields.Boolean(string='Check Bounce Invoice', default=False)

    def remove_sale_commission(self):

        for invoice in self:
            commission_rec = self.env['sale.commission'].search([
                ('invoice_id', '=', invoice.id), ('is_paid', '=', True),
                ('is_cancelled', '=', False), ('invoice_type', '=', 'out_invoice')])
            for rec in commission_rec:
                if rec.is_settled:
                    rec.is_cancelled = True
                    sale = invoice.invoice_line_ids.mapped('sale_line_ids')
                    commission = rec.commission
                    vals1 = {
                            'sale_person_id' : rec.sale_person_id.id,
                            'sale_id': sale and sale[-1].order_id.id,
                            'commission': -commission,
                            'invoice_id' : invoice.id,
                            'invoice_type' : 'bounced_cheque',
                            'is_paid':True,
                            'invoice_amount':invoice.amount_total,
                            'commission_date': date.today()
                            }
                    refund_rec = self.env['sale.commission'].create(vals1)
                    vals2 = {
                            'sale_person_id' : rec.sale_person_id.id,
                            'sale_id': sale and sale[-1].order_id.id,
                            'commission': commission,
                            'invoice_id' : invoice.id,
                            'invoice_type' : 'out_invoice',
                            'is_paid':False,
                            'invoice_amount':invoice.amount_total,
                            'commission_date': self.date_invoice and self.date_invoice
                            }
                    new_rec = self.env['sale.commission'].create(vals2)
                else:
                    rec.is_paid = False
            check_bounce_product = invoice.company_id.check_bounce_product or False
            if not check_bounce_product:
                raise UserError(_('Check Bounce Product is not configured in Company'))

            fpos = invoice.fiscal_position_id
            account = check_bounce_product.product_tmpl_id.get_product_accounts(fpos)
            if account and account.get('income',''):
                account = account['income']
            line_vals = [(0,0,{
                         'name': 'Check Bounce Fine',
                         'account_id': account.id,
                         'product_id':check_bounce_product.id,
                         'price_unit': check_bounce_product.lst_price,
                         'quantity': 1.0,
                         'discount': 0.0,
                        })]

            invoice_vals = {
                'type': 'out_invoice',
                'reference': False,
                'account_id': invoice.account_id.id,
                'partner_id': invoice.partner_id.id,
                'partner_shipping_id': invoice.partner_shipping_id.id,
                'invoice_line_ids': line_vals,
                'currency_id': invoice.currency_id.id,
                'payment_term_id': invoice.payment_term_id.id,
                'fiscal_position_id': invoice.fiscal_position_id and invoice.fiscal_position_id.id,
                'team_id': invoice.team_id.id,
                'check_bounce_invoice': True
            }
            invoice_fine = self.env['account.invoice'].create(invoice_vals)
        return True


Accountinvoice()
