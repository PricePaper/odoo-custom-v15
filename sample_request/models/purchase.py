# -*- coding: utf-8 -*-
from odoo import api, models, fields,SUPERUSER_ID, _
from odoo.exceptions import UserError




class PurchaseOrder(models.Model):
    _inherit = "purchase.order"


    def _activity_cancel_on_sale(self):
        if not self._context.get('sample_order'):
            return super(PurchaseOrder, self)._activity_cancel_on_sale()
            
        

    def _sample_prepare_picking(self):
        if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.origin,
                'partner_id': self.partner_id.id
            })
        if not self.partner_id.property_stock_supplier.id:
            raise UserError(_("You must set a Vendor Location for this partner %s", self.partner_id.name))
        return {
            'picking_type_id': self.picking_type_id.id,
            'partner_id': self.partner_id.id,
            'user_id': False,
            'date': self.date_order,
            'origin': self.origin,
            'location_dest_id': self._get_destination_location(),
            'location_id': self.partner_id.property_stock_supplier.id,
            'company_id': self.company_id.id,
        }


    def _create_sample_request_picking(self):
        StockPicking = self.env['stock.picking']
        for order in self:
            if any(product.type in ['product', 'consu'] for product in order.order_line.product_id):
                order = order.with_company(order.company_id)
                pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                if not pickings:
                    res = order._sample_prepare_picking()
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

