# -*- coding: utf-8 -*-

from odoo import fields, models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    picking_partner_id = fields.Many2one('res.partner', related='picking_id.partner_id', string='Partner')
    
    def _search_picking_for_assignation(self):
        """
        Overriden to create one DO per one SO.
        """
        self.ensure_one()
        picking = self.env['stock.picking'].search([
                ('group_id', '=', self.group_id.id),
                ('location_dest_id', '=', self.location_dest_id.id),
                ('picking_type_id', '=', self.picking_type_id.id),
                ('printed', '=', False),
                ('state', 'in', ['draft', 'confirmed', 'waiting', 'partially_available', 'assigned'])], limit=1)
        return picking


StockMove()

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    picking_partner_id = fields.Many2one('res.partner', related='move_id.picking_partner_id', string='Partner')




StockMoveLine()
