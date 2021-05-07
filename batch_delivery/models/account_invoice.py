# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    picking_ids = fields.Many2many('stock.picking', compute='_compute_picking_ids', string='Pickings')

    @api.depends('invoice_line_ids.stock_move_ids.picking_id')
    def _compute_picking_ids(self):
        for rec in self:
            rec.picking_ids = rec.invoice_line_ids.mapped('stock_move_ids').mapped('picking_id')

    @api.multi
    def name_get(self):
        result = []
        if self._context.get('from_batch_payment', False):
            for invoice in self:
                result.append((invoice.id, '%s ( %s )' % (invoice.number, invoice.residual)))
            return result
        return super(AccountInvoice, self).name_get()

    @api.multi
    def action_view_picking(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]

        pickings = self.mapped('picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action

    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        if not self:
            return res
        stock_picking = self.env['stock.picking']
        for pick in self.mapped('picking_ids').filtered(lambda pick: pick.state != 'done'):
            if pick._check_backorder():
                move_info = pick.move_ids_without_package.filtered(lambda m: m.quantity_done < m.product_uom_qty)
                default_reason = self.env.ref('batch_delivery.default_stock_picking_return_reason', raise_if_not_found=False)
                if default_reason:
                    move_info.write({'reason_id': default_reason.id})
                stock_picking |= pick
            else:
                pick.action_done()
        wiz = self.env['stock.backorder.confirmation'].create({'pick_ids': [(4, p.id) for p in stock_picking]})
        wiz.process_cancel_backorder()
        return res

    @api.model
    def default_get(self,default_fields):
        result = super(AccountInvoice, self).default_get(default_fields)
        result['date_invoice'] = fields.Date.today()
        return result

    @api.model
    def create(self, vals):
        invoice = super(AccountInvoice, self).create(vals)
        if not invoice.move_name or not invoice.number:
            if invoice.journal_id and invoice.journal_id.sequence_id:
                new_name = invoice.journal_id.sequence_id.with_context(ir_sequence_date=invoice.date_invoice or fields.Date.today()).next_by_id()
                invoice.write({'number': new_name, 'move_name': new_name})
        return invoice

    @api.multi
    def action_invoice_sent(self):
        self.ensure_one()
        template = self.env.ref('account.email_template_edi_invoice', False)
        report_template = self.env.ref('batch_delivery.ppt_account_selected_invoices_with_payment_report')
        if template and report_template and template.report_template.id != report_template.id:
            template.write({'report_template': report_template.id})
        return super(AccountInvoice, self).action_invoice_sent()

AccountInvoice()


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    stock_move_ids = fields.Many2many('stock.move', string="Stock Moves")
    line_number = fields.Integer()


AccountInvoiceLine()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
