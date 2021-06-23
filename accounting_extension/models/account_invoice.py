# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    discount_date = fields.Date('Discount Till')

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        if self.payment_term_id and self.payment_term_id.is_discount:
            invoice_date = self.date_invoice
            self.discount_date = invoice_date + relativedelta(days=self.payment_term_id.due_days)
        return res

    @api.multi
    def action_cancel_draft(self):
        self.ensure_one()
        res = super(AccountInvoice, self).action_cancel_draft()
        vals = {'discount_date': False}
        if self.move_name:
            vals.update({'number': self.move_name})
        self.write(vals)
        return res

    def action_invoice_draft(self):
        self.ensure_one()
        res = super(AccountInvoice, self).action_invoice_draft()
        if self.move_name:
            self.write({'number': self.move_name})
        return res

    @api.multi
    def action_cancel_old(self):
        res = super(AccountInvoice, self).action_cancel()
        self.write({'move_name': False})
        return res

    def update_journal(self, offset=0, limit=10000):        
        for aml in self.env['account.move.line'].search([('account_id', '=', 6), ('journal_id', '=', 6), ('debit', '>', 0)], offset=offset, limit=limit):
            if aml.move_id.stock_move_id:
                invoice_line =  self.env['account.invoice.line'].search([('stock_move_ids', 'in', aml.move_id.stock_move_id.id)])
                if not invoice_line:
                    pick = self.env['stock.picking'].search([('name', '=', aml.move_id.ref)])
                    invoice_line = pick.sale_id.invoice_ids.filtered(lambda rec: rec.state not in ('cancel', 'draft')).mapped('invoice_line_ids').filtered(lambda r: r.product_id.id == aml.product_id.id)
                for line in invoice_line:
                    invoice = line.mapped('invoice_id')
                    move = invoice.move_id
                    i=0
                    for c_aml in move.line_ids.filtered(lambda rec: rec.product_id.id == line.product_id.id and rec.product_id is not False and rec.account_id.id == 6):
                        i += 1                        
                        if c_aml.account_id.id == aml.account_id.id and c_aml.credit != aml.debit and aml.debit != 0 and c_aml.credit > 0:
                            cogs = move.line_ids.filtered(lambda rec: rec.product_id.id == line.product_id.id and rec.product_id is not False and rec.account_id.id == 725 and rec.debit == c_aml.credit and rec.debit > 0)
                            if len(cogs) > 1:
                                cogs = cogs[0]
                            if cogs:
                                # print(aml.debit,c_aml.debit,c_aml.credit,cogs.debit, cogs, aml,c_aml)
                                # print("update account_move_line set balance=%s,credit_cash_basis=%s,balance_cash_basis=%s,credit=%s where id=%s" % (aml.debit * -1, aml.debit, aml.debit * -1, aml.debit, c_aml.id))
                                # print("update account_move_line set debit_cash_basis=%s,balance_cash_basis=%s,balance=%s,debit=%s where id=%s" % (aml.debit, aml.debit, aml.debit, aml.debit, cogs.id))
                                self.env.cr.execute("update account_move_line set balance=%s,credit_cash_basis=%s,balance_cash_basis=%s,credit=%s where id=%s", (aml.debit * -1, aml.debit, aml.debit * -1, aml.debit, c_aml.id))
                                self.env.cr.execute("update account_move_line set debit_cash_basis=%s,balance_cash_basis=%s,balance=%s,debit=%s where id=%s", (aml.debit, aml.debit, aml.debit, aml.debit, cogs.id))                                
                                self.env.cr.commit() 
                                # print(aml.debit,c_aml.credit,cogs.debit, cogs, aml,c_aml)
                                # # if input('sssssssss') == 'y':print(o)
                            else:
                                a = open('journal_balance.csv', 'a+')
                                a.write("%s,%s,%s,'no cogs to correct'\n" % (aml.name, c_aml.name, move.name))
                                a.close()        
                                # print('cogs not found', aml, c_aml)  
                            # if c_aml.date != aml.date:
                            #     print("\t\t\tupdate account_move_line set date='%s' where id=%s"% (c_aml.date, aml.id))
                            #     self.env.cr.execute("update account_move_line set date=%s where id=%s", (c_aml.date, aml.id))
                            #     self.env.cr.commit()
                                # aml.write({'date': c_aml.date})     
                        continue            
                if not invoice_line:
                    a = open('journal_balance.csv', 'a+')
                    a.write("%s,%s,'no invoice to correct the amount'\n" % (aml.name, aml.move_id.name))
                    a.close()                            

    def correct_date(self, offset=0, limit=10000):        
        for move in self.env['account.move'].search([('journal_id', '=', 6), ('date', '<', '2021-07-01')], offset=offset, limit=limit):
            order = move.stock_move_id.picking_id.sale_id
            invoice_line = self.env['account.invoice.line'].search([('stock_move_ids', 'in', move.stock_move_id.ids)])
            invoice = invoice_line.mapped('invoice_id')
            if not invoice:
                pick = self.env['stock.picking'].search([('name', '=', move.ref)])
                invoice = pick.sale_id.invoice_ids.filtered(lambda rec: rec.state not in ('cancel', 'draft'))
                # .mapped('invoice_line_ids').filtered(lambda r: r.product_id.id == aml.product_id.id)
            if len(invoice) != 1:
                a = open('date_correct.csv', 'a+')
                a.write("%s,%s, 'multiple invoice'\n" % (move.name, order.name or ''))
                a.close()
                continue
            aml = invoice.move_id
            if not aml:
                a = open('issues.csv', 'a+')
                a.write("%s,%s,'aml not found in invoice'\n" % (move.name, order.name or ''))
                a.close()
                continue
            if aml.date != move.date:
                # print("update account_move set date=%s where id=%s" %(aml.date, move.id))
                self.env.cr.execute("update account_move set date=%s where id=%s", (aml.date, move.id))
                self.env.cr.execute("update account_move_line set date=%s where move_id=%s", (aml.date, move.id))
                self.env.cr.commit()