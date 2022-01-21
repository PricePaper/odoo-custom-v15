# -*- coding: utf-8 -*-

from odoo import fields, models


class StockMoveLocation(models.Model):
    _name = "stock.move.by.location"
    _description = "Location Moves"
    _auto = False

    id = fields.Char(string='id', readonly=True)
    description = fields.Char(string='Description', readonly=True)
    location_id = fields.Many2one('stock.location', string='Location', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    categ_id = fields.Many2one(related='product_id.categ_id', string='Category',
                               readonly=True)
    name = fields.Float(string='Quantity', digits=(16, 2), readonly=True)
    uom_id = fields.Many2one(related='product_id.uom_id', string="UoM", readonly=True)
    product_qty_pending = fields.Float(string='Quantity Pending', digits=(16, 2), readonly=True)
    date = fields.Datetime(string='Date Planned', readonly=True)
    picking_id = fields.Many2one('stock.picking', string='Packing', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)

    def init(self):
        self.env.cr.execute("""create or replace view stock_move_by_location
as
select i.id ,
 l.id as location_id,product_id,
 i.name as description,
 case when state ='done' then product_qty else 0 end as name,
 case when state !='done' then product_qty else 0 end as product_qty_pending,
 date,
 picking_id,l.company_id
from stock_location l,
     stock_move i
where l.usage='internal'
  and i.location_dest_id = l.id
  and state != 'cancel'
  and i.company_id = l.company_id
union all
select -o.id ,
l.id as location_id ,product_id,
 o.name as description,
 case when state ='done' then -product_qty else 0 end as name,
 case when state !='done' then -product_qty else 0 end as product_qty_pending,
 date,
 picking_id,l.company_id
from stock_location l,
     stock_move o
where l.usage='internal'
  and o.location_id = l.id
  and state != 'cancel'
  and o.company_id = l.company_id
;""")


