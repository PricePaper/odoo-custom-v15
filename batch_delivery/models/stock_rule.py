from odoo import api, fields, models


class StockRule(models.Model):
    _inherit = 'stock.rule'


    @api.model
    def run(self, procurements, raise_user_error=True):
        if self._context.get('reset_po_line_id'):
            moves = procurements.get('move_dest_ids')
            po_line = self.env['purchase.order.line'].browse(self._context.get('reset_po_line_id'))
            moves.write({'created_purchase_line_id': po_line.id, 'move_orig_ids': [6, 0, po_line.move_ids.ids]})
            return True
        return super(StockRule, self).run(procurements, raise_user_error=raise_user_error)
