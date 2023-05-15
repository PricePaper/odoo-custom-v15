# -*- coding: utf-8 -*-
from odoo import api, models, fields,SUPERUSER_ID, _




class PurchaseOrder(models.Model):
    _inherit = "purchase.order"


    def _activity_cancel_on_sale(self):
        if not self._context.get('sample_order'):
            import pdb 
            pdb.set_trace()
            return super(PurchaseOrder, self)._activity_cancel_on_sale()
            
        

    # def 


    def _create_sample_request_picking(self):
        StockPicking = self.env['stock.picking']
        for order in self:
            if any(product.type in ['product', 'consu'] for product in order.order_line.product_id):
                order = order.with_company(order.company_id)
                pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                if not pickings:
                    res = order._prepare_picking()
                    picking = StockPicking.with_user(SUPERUSER_ID).create(res)
                else:
                    picking = pickings[0]
                moves = order.order_line._create_stock_moves(picking)
                moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                seq = 0
                for move in sorted(moves, key=lambda move: move.date):
                    seq += 5
                    move.sequence = seq
                moves._action_assign()
                
        return True

