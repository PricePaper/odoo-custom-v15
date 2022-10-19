from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero



class StockPicking(models.Model):
    _inherit = 'stock.picking'


    def validate_multiple_delivery(self):
        for rec in self:
            if rec.state not in ('in_transit', 'transit_confirmed') and not rec.rma_id and not rec.purchase_id:
                raise UserError(_(
                    "Some of the selected Delivery order is not in transit state"))
            rec.button_validate()
        return {'type': 'ir.actions.act_window_close'}


class StockMove(models.Model):
    _inherit = 'stock.move'


    def _get_price_unit(self):
        """ Override to return RMA moves's price"""
        self.ensure_one()
        if self.picking_id and self.picking_id.rma_id:
            original_move = self.sale_line_id.move_ids.filtered(lambda r: r.picking_code == 'outgoing')
            if original_move:
                layers = original_move.sudo().stock_valuation_layer_ids
                if layers:
                    quantity = sum(layers.mapped("quantity"))
                    if not float_is_zero(quantity, precision_rounding=layers.uom_id.rounding):
                        return  layers.currency_id.round(sum(layers.mapped("value")) / quantity)
        return super(StockMove, self)._get_price_unit()
