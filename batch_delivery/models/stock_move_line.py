# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    pref_lot_id = fields.Many2one('stock.production.lot', string='Preferred Lot')
    is_transit = fields.Boolean(related='move_id.is_transit', readonly=True)

    def _free_reservation(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None, ml_ids_to_ignore=None):
        if self._context.get('from_inv_adj', False):
            in_transit_move_lines_domain = [
                ('state', 'not in', ['done', 'cancel']),
                ('product_id', '=', product_id.id),
                ('lot_id', '=', lot_id.id if lot_id else False),
                ('location_id', '=', location_id.id),
                ('owner_id', '=', owner_id.id if owner_id else False),
                ('package_id', '=', package_id.id if package_id else False),
                ('product_qty', '>', 0.0),
                ('id', 'not in', ml_ids_to_ignore),
                ('is_transit', '=', True),
            ]
            in_transit_candidates = self.env['stock.move.line'].search(in_transit_move_lines_domain)
            if ml_ids_to_ignore is None:
                ml_ids_to_ignore = []
            ml_ids_to_ignore += in_transit_candidates.ids
        return super()._free_reservation(product_id, location_id, quantity, lot_id=lot_id,
                                         package_id=package_id, owner_id=owner_id,
                                         ml_ids_to_ignore=ml_ids_to_ignore)

    @api.model
    def create(self, vals):
        result = super(StockMoveLine, self).create(vals)
        if 'qty_done' in vals:
            result.move_id.update_invoice_line()
        return result

    def write(self, vals):
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
