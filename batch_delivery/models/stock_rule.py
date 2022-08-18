from odoo import api, fields, models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.model
    def _run_buy(self, procurements):
        """
        Override to check if this is reset button click from delivery order
        Then we dont need to create a new Po just link the existing Po with the new Delivery order
        """
        if self._context.get('reset_po_line_id'):
            for procurement, rule in procurements:
                moves = procurement.values.get('move_dest_ids')
                po_line = self.env['purchase.order.line'].browse(self._context.get('reset_po_line_id')[0])
                vals = {}
                # context value contains a tuple either the recipt move id or the po line, update move based on the value
                if self._context.get('reset_po_line_id')[0]:
                    vals.update({'created_purchase_line_id': po_line.id })
                if self._context.get('reset_po_line_id')[1]:
                    vals.update({'move_orig_ids': [[6, 0, self._context.get('reset_po_line_id')[1]]]})
                moves.write(vals)
                # reset the context value, don't want to break the child operations
                self = self.with_context({'reset_po_line_id': False})
            return True
        return super(StockRule, self)._run_buy(procurements)
