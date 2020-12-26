from odoo import fields, models, api


class PendingProductView(models.TransientModel):
    _name = 'pending.product.view'
    _description = 'Pending Product View'

    @api.model
    def _get_default_batch(self):
        if self._context.get('active_ids'):
            batch = self.env['stock.picking.batch'].browse(self._context.get('active_ids'))
            return [(6, 0, batch.ids)]

    batch_ids = fields.Many2many("stock.picking.batch", default=_get_default_batch)

    def generate_move_lines(self):
        """
        Extract the pickings from batch and filtered out the pending move lines.
        """
        # consider the picking as in transit state to recalculate on hand qty with updated qty.
        # make move state in transit for calculation on hand quantity
        self.batch_ids.mapped('picking_ids').action_make_transit()
        move_lines = self.batch_ids.mapped('picking_ids').filtered(
            lambda pick: pick.state not in ['done', 'cancel']
        ).mapped('move_lines').ids

        action = self.env['ir.actions.act_window'].for_xml_id('batch_delivery', 'stock_move_pending_product_action')
        action['domain'] = [('id', 'in', move_lines)]

        return action


PendingProductView()
