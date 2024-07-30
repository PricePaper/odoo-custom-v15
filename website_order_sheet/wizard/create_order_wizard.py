# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import pytz

class CreateOrder_main(models.TransientModel):
    _name = 'create.order.main'
    _description = "Wizard For creating order from Order Sheet"



    def create_main_order(self):
        
        partner_id = self.sheet_id.partner_id.id
       
        sale_vals = {
            'partner_id':partner_id,
                'invoice_address_id':partner_id,
                'partner_shipping_id':partner_id,
                'order_line':[(0,0,
                {'product_id':res.product_id.id,
                'product_uom':res.uom_id.id,
                'product_uom_qty':res.qty,'sales_person_ids':[(6,0,self.sheet_id.partner_id.sales_person_ids.ids)]})for res in self.create_order_ids if res.qty > 0]

        }
        sale_id = self.env['sale.order'].sudo().create(sale_vals)

        return {'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_id': sale_id.id,
            'res_model': "sale.order",
            'target': 'self',
            # 'context': context,
            }



    
    sheet_id = fields.Many2one('website.order.sheet',sting='Sheet')
    create_order_ids = fields.One2many('create.order', 'create_order_main_id', string='Create Order')



class CreateOrder(models.TransientModel):
    _name = 'create.order'
    _description = "Wizard For creating order from Order Sheet"
    
    create_order_main_id = fields.Many2one("create.order.main",string="Create Main Order")

    name = fields.Char(string='Section Name')
    product_id = fields.Many2one('product.product',sting='Product')
    sale_uoms = fields.Many2many('uom.uom',related="product_id.sale_uoms")
    uom_id = fields.Many2one("uom.uom",string='UOM')
    qty = fields.Integer(string="Quantity")
#     section_product_ids = fields.One2many('create.order.line', 'order_line_id', string='Section Product')

# class CreateOrderLines(models.TransientModel):
#     _name = "create.order.line"
#     _rec_name="product_id"
    
#     order_line_id = fields.Many2one('create.order',string="Order Line")