# -*- coding: utf-8 -*-

from odoo import models, api, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        res = super(StockMove, self)._prepare_merge_moves_distinct_fields()
        if self._context.get('from_purchase_write'):
            if 'price_unit' in res:
                res.remove('price_unit')
            if 'propagate_cancel' in res:
                res.remove('propagate_cancel')
        return res


StockMove()


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.depends('move_lines.date_deadline', 'move_type')
    def _compute_date_deadline(self):
        for picking in self:
            if picking.move_type == 'direct':
                picking.date_deadline = min(picking.move_lines.filtered('date_deadline').mapped('date_deadline'), default=False)
                if picking.picking_type_code == 'incoming' and not picking.is_return:
                    picking.date_deadline = max(picking.move_lines.filtered('date_deadline').mapped('date_deadline'), default=False)
            else:
                picking.date_deadline = max(picking.move_lines.filtered('date_deadline').mapped('date_deadline'), default=False)


    def _log_activity_get_documents_old(self, orig_obj_changes, stream_field, stream, sorted_method=False, groupby_method=False):
        """
        For PO line qty chnage to reflect in the Stock picking
        """
        res = super(StockPicking, self)._log_activity_get_documents(orig_obj_changes, stream_field, stream, sorted_method=sorted_method,
                                                                    groupby_method=groupby_method)
        result = {}
        if list(orig_obj_changes.keys())[0]._name == 'purchase.order.line' and stream == 'DOWN':
            for picking, moves in res.items():
                if picking[0].state not in ('done', 'cancel'):
                    for move, qty in moves.items():
                        if move.state not in ('done', 'cancel'):
                            move.product_uom_qty = qty[1][0]
                        else:
                            if picking in result:
                                result[picking][move] = qty
                            else:
                                result[picking] = {move: qty}
                else:
                    result[picking] = moves
        return result or res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
