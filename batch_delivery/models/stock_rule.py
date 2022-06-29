from odoo import api, fields, models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.model
    def _run_buy(self, procurements):
        if self._context.get('reset_po_line_id'):
            for procurement, rule in procurements:
                moves = procurement.values.get('move_dest_ids')
                po_line = self.env['purchase.order.line'].browse(self._context.get('reset_po_line_id')[0])
                vals = {}
                if self._context.get('reset_po_line_id')[0]:
                    vals.update({'created_purchase_line_id': po_line.id })
                if self._context.get('reset_po_line_id')[1]:
                    vals.update({'move_orig_ids': [[6, 0, self._context.get('reset_po_line_id')[1]]]})
                print(vals)
                moves.write(vals)
                self = self.with_context({'reset_po_line_id': False})
            return True
        print('pani pali', self._context)
        return super(StockRule, self)._run_buy(procurements)
