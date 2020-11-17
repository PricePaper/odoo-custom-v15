# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError



class Accountinvoice(models.Model):
    _inherit = "account.invoice"

    def remove_sale_commission(self):

        invoice_num = len(self)
        fine_amount = 30
        if invoice_num > 1:
            fine_amount = 30/invoice_num
        for invoice in self:
            commission_rec = self.env['sale.commission'].search([('invoice_id', '=', invoice.id), ('is_paid', '=', True), ('invoice_type', '=', 'out_invoice')])
            for rec in commission_rec:
                if rec.is_settled:
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
            invoice.with_context(from_check_bounce=True).action_invoice_cancel()
            invoice.action_invoice_draft()
            invoice.state = 'draft'
            line_vals = {'invoice_id':invoice.id,
                         'name': 'Check Bounce Fine',
                         'account_id': account.id,
                         'product_id':check_bounce_product.id,
                         'price_unit': fine_amount,
                         'quantity': 1.0,
                         'discount': 0.0,
                        }
            fine_line = self.env['account.invoice.line'].create(line_vals)
            invoice.action_invoice_open()
        return True


Accountinvoice()
