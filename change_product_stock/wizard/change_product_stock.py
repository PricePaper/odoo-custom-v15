# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import date
from odoo.exceptions import UserError

class ChangeProductStock(models.TransientModel):
    _name = 'change.product.stock'
    _description = 'Change Product Stock'

    dest_product_id = fields.Many2one('product.product', string='Destination Product')
    source_product_id = fields.Many2one('product.product', string='Source Product')
    qty = fields.Float(string='Qty')
    stock_valuation_layer_ids = fields.Many2many('stock.valuation.layer', compute='_compute_stock_valuation', string="Stock Valuation Layer")
    stock_valuation_layer_id = fields.Many2one('stock.valuation.layer', string='Selected move', compute='_compute_stock_valuation')

    @api.depends('source_product_id')
    def _compute_stock_valuation(self):
        for rec in self:
            rec.stock_valuation_layer_ids = False
            rec.stock_valuation_layer_id = False
            if rec.source_product_id:
                stock_value_ids = rec.source_product_id.stock_valuation_layer_ids.filtered(lambda r: r.remaining_qty > 0)
                if stock_value_ids:
                    rec.stock_valuation_layer_ids = [(6, 0, stock_value_ids.ids)]
                    rec.stock_valuation_layer_id = stock_value_ids.sorted('create_date')[0]


    def _get_inventory_move_values(self, quant, qty, location_id, location_dest_id, out=False):
        """
        return move vals
        """
        name = _('Product Quantity Updated')
        return {
            'name': name,
            'product_id': quant.product_id.id,
            'product_uom': self.stock_valuation_layer_id.uom_id.id,
            'product_uom_qty': qty,
            'company_id': quant.company_id.id or self.env.company.id,
            'state': 'confirmed',
            'location_id': location_id.id,
            'location_dest_id': location_dest_id.id,
            'is_inventory': True,
            'price_unit': self.stock_valuation_layer_id.unit_cost,
            'date': self.stock_valuation_layer_id.create_date,
            'move_line_ids': [(0, 0, {
                'product_id': quant.product_id.id,
                'product_uom_id': self.stock_valuation_layer_id.uom_id.id,
                'qty_done': qty,
                'location_id': location_id.id,
                'location_dest_id': location_dest_id.id,
                'company_id': quant.company_id.id or self.env.company.id,
                'lot_id': quant.lot_id.id,
                'package_id': out and quant.package_id.id or False,
                'result_package_id': (not out) and quant.package_id.id or False,
                'owner_id': quant.owner_id.id,
            })]
        }

    def change_stock(self):
        Quant = self.env['stock.quant']
        source_quant = Quant.search([('product_id', '=', self.source_product_id.id), ('location_id', '=', self.source_product_id.property_stock_location.id)])
        if self.qty <= 0:
            raise UserError(_('Please insert qty'))
        if self.qty > self.stock_valuation_layer_id.remaining_qty:
            raise UserError(_('Please insert qty less than valuation Layer remaining qty'))
        if self.qty > source_quant.product_uom_id._compute_quantity(source_quant.available_quantity, self.stock_valuation_layer_id.uom_id):
            raise UserError(_('Product location does not have enough qty'))
        dest_quant = Quant.search([('product_id', '=', self.dest_product_id.id), ('location_id', '=', self.dest_product_id.property_stock_location.id)])
        out_move_vals = self._get_inventory_move_values(source_quant, self.qty,
                                         source_quant.location_id,
                                         source_quant.product_id.with_company(source_quant.company_id).property_stock_inventory,
                                         out=True)

        in_move_vals = self._get_inventory_move_values(dest_quant, self.qty,
                                         dest_quant.product_id.with_company(dest_quant.company_id).property_stock_inventory,
                                         dest_quant.location_id)

        out_move = self.env['stock.move'].with_context(inventory_mode=False, from_inv_adj=True).create(out_move_vals)
        in_move = self.env['stock.move'].with_context(inventory_mode=False, from_inv_adj=True).create(in_move_vals)
        in_move.price_unit = in_move.product_uom._compute_price(in_move.price_unit, in_move.product_id.ppt_uom_id)




        out_move._action_done()
        source_quant.location_id.write({'last_inventory_date': fields.Date.today()})
        date_by_location = {loc: loc._get_next_inventory_date() for loc in source_quant.mapped('location_id')}
        source_quant.inventory_date = date_by_location[source_quant.location_id]
        source_quant.product_id.last_inventoried_date = date.today()
        self._cr.execute("UPDATE stock_valuation_layer set create_date = '%s' WHERE id=%s" % (self.stock_valuation_layer_id.create_date, out_move.stock_valuation_layer_ids.ids[0]))

        in_move._action_done()
        dest_quant.location_id.write({'last_inventory_date': fields.Date.today()})
        date_by_location = {loc: loc._get_next_inventory_date() for loc in dest_quant.mapped('location_id')}
        dest_quant.inventory_date = date_by_location[dest_quant.location_id]
        dest_quant.product_id.last_inventoried_date = date.today()

        self._cr.execute("UPDATE stock_valuation_layer set create_date = '%s' WHERE id=%s" % (self.stock_valuation_layer_id.create_date, in_move.stock_valuation_layer_ids.ids[0]))
