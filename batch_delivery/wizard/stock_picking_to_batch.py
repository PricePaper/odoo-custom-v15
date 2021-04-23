# -*- coding: utf-8 -*-

from odoo import api, fields, models


class StockPickingToBatch(models.TransientModel):
    _inherit = 'stock.picking.to.batch'


    @api.multi
    def attach_pickings(self):
        # use active_ids to add picking line to the selected batch
        self.ensure_one()
        picking_ids = self.env.context.get('active_ids')
        return self.env['stock.picking'].browse(picking_ids).write({
            'batch_id': self.batch_id.id,
            'route_id': self.batch_id.route_id.id
        })
