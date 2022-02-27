# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    rma_id = fields.Many2one('rma.ret.mer.auth', string='RMA')
    rma_done = fields.Boolean("RMA is Done", copy=False)

    def _action_done(self):
        # Don't allow to validate outgoing picking before validating incoming in case of exchange.
        for picking in self.filtered(lambda p: p.rma_id):
            incoming_pickings = picking.rma_id.stock_picking_ids.filtered(
                lambda p: p.picking_type_code == 'incoming' and p.id != picking.id
            )
            if incoming_pickings and any(p.state != 'done' for p in incoming_pickings):
                raise UserError(_('Outgoing picking cannot be done before validating incoming picking.'))
        res = super(StockPicking, self)._action_done()
        # Unlink return picking created by odoo, when exchange of products.
        for picking in self.filtered(lambda p: p.picking_type_code == 'outgoing' and p.rma_id and p.rma_id.sale_order_id and p.sale_id):
            sale_order = picking.sale_id
            warehouse = sale_order.warehouse_id
            if warehouse:
                return_picking_type = warehouse.return_type_id
                return_picking_to_remove = sale_order.picking_ids.filtered(
                    lambda p: p.picking_type_id.id == return_picking_type.id
                    and p.state not in ['done', 'cancel']
                )
                return_picking_to_remove.sudo().action_cancel()
                return_picking_to_remove.sudo().unlink()
        return res


class StockMove(models.Model):
    _inherit = 'stock.move'

    rma_id = fields.Many2one('rma.ret.mer.auth', string='RMA')
