# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    delivery_move_line_id = fields.Many2one(
        'stock.move.line', string='Delivery Move line For')
    delivery_picking_id = fields.Many2one(
        'stock.picking', string='Delivery for Picking', readonly=True, related='delivery_move_line_id.picking_id')
    pref_lot_id = fields.Many2one('stock.production.lot', string='Preferred Lot')
    is_transit = fields.Boolean(related='move_id.is_transit', readonly=True)

    @api.multi
    def write(self, vals):
        result = super(StockMoveLine, self).write(vals)
        for line in self:
            sale_line = line.move_id.sale_line_id

            if 'qty_done' in vals and sale_line:
                qty = vals['qty_done']
                invoice_lines = sale_line.invoice_lines.filtered(
                    lambda rec: rec.invoice_id.state != 'cancel' and line.move_id in rec.stock_move_ids)
                invoices = invoice_lines.mapped('invoice_id')
                if invoice_lines:
                    invoice_lines.write({'quantity': qty})
                    if qty == 0:

                        invoice_lines.sudo().unlink()
                        invoices.compute_taxes()

                        delivery_inv_lines = self.env['account.invoice.line']
                        # if a invoice have only one line we need to make sure it's not a delivery change.
                        # if its a devlivery change, remove it from invoice  and cancel the entry.
                        for invoice in invoices:
                            if len(invoice.invoice_line_ids) == 1:
                                if all(invoice.invoice_line_ids.mapped('sale_line_ids').mapped('is_delivery')):
                                    delivery_inv_lines |= invoice.invoice_line_ids

                        if delivery_inv_lines:
                            delivery_inv_lines.sudo().unlink()

                        amount = sum(invoices.mapped('amount_total'))

                        if not amount:
                            invoices.sudo().action_invoice_cancel()

                    else:
                        invoice_lines.mapped('invoice_id').compute_taxes()

                sale_line.qty_delivered = qty

            if 'picking_id' in vals:
                sale_line.invoice_lines.filtered(lambda rec: line.move_id in rec.stock_move_ids).sudo().unlink()

        return result

    @api.multi
    def unlink(self):
        for line in self:
            sale_line = line.move_id.sale_line_id
            if sale_line:
                invoice_lines = sale_line.invoice_lines.filtered(
                    lambda rec: rec.invoice_id.state != 'cancel' and line.move_id in rec.stock_move_ids)

                if invoice_lines:
                    invoices = invoice_lines.mapped('invoice_id')
                    invoice_lines.sudo().unlink()
                    invoices.compute_taxes()

                    delivery_inv_lines = self.env['account.invoice.line']
                    # if a invoice have only one line we need to make sure it's not a delivery change.
                    # if its a devlivery change, remove it from invoice  and cancel the entry.
                    for invoice in invoices:
                        if len(invoice.invoice_line_ids) == 1:
                            if all(invoice.invoice_line_ids.mapped('sale_line_ids').mapped('is_delivery')):
                                delivery_inv_lines |= invoice.invoice_line_ids

                    if delivery_inv_lines:
                        delivery_inv_lines.sudo().unlink()

                    amount = sum(invoices.mapped('amount_total'))

                    if not amount:
                        invoices.sudo().action_invoice_cancel()

        result = super(StockMoveLine, self).unlink()
        return result


StockMoveLine()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
