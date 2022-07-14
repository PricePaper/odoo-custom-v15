# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    pref_lot_id = fields.Many2one('stock.production.lot', string='Preferred Lot')
    # is_transit = fields.Boolean(related='move_id.is_transit', readonly=True)

    @api.model
    def create(self, vals):
        result = super(StockMoveLine, self).create(vals)
        if 'qty_done' in vals:
            result.move_id.update_invoice_line()
        return result

    def write(self, vals):
        if 'product_uom_qty' in vals and vals.get('product_uom_qty', 0) != 0:
            if len(self.ids) == 1 and self.product_uom_id != self.product_id.uom_id:
                ordered = sum(self.move_id.mapped('product_uom_qty'))
                reserved = sum((self.move_id.move_line_ids - self).mapped('product_uom_qty'))
                pending = ordered-reserved
                if pending != vals['product_uom_qty']:
                    vals['product_uom_qty'] = pending
        result = super(StockMoveLine, self).write(vals)
        if 'qty_done' in vals:
            for line in self.mapped('move_id'):
                line.update_invoice_line()
        return result

    def unlink(self):
        moves = self.mapped('move_id')
        result = super(StockMoveLine, self).unlink()
        for line in moves:
            line.update_invoice_line()
        return result
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
