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
            if vals.get('qty_done') and sale_line:
                invoice_lines = sale_line.invoice_lines.filtered(
                    lambda rec: rec.invoice_id.state != 'cancel' and line.move_id in rec.stock_move_ids)
                if invoice_lines:
                    invoice_lines.write({'quantity': vals.get('qty_done')})
                    invoice_lines.mapped('invoice_id').compute_taxes()
                sale_line.qty_delivered = sale_line.pre_delivered_qty + vals.get('qty_done')

            if 'picking_id' in vals:
                sale_line.invoice_lines.filtered(lambda rec: line.move_id in rec.stock_move_ids).unlink()

        return result

    @api.multi
    def unlink(self):
        for line in self:
            sale_line = line.move_id.sale_line_id
            if sale_line:
                invoice_lines = sale_line.invoice_lines.filtered(
                    lambda rec: rec.invoice_id.state != 'cancel' and line.move_id in rec.stock_move_ids)
                if invoice_lines:
                    invoice_lines.write({'quantity': 0})
                    invoice_lines.mapped('invoice_id').compute_taxes()
        result = super(StockMoveLine, self).unlink()
        return result

StockMoveLine()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
