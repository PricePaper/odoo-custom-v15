# -*- coding: utf-8 -*-

from odoo import models, fields, api


class WebsiteOrderSheet(models.Model):
    _name = "website.order.sheet"
    _description='Model for managing user order sheet'
    

    name = fields.Char(string='Name')
    user_id = fields.Many2one('res.users','User')
    order_lines = fields.One2many('order.sheet.lines','sheet_id',string='Order Lines')


class OrderSheetLines(models.Model):
    _name = "order.sheet.lines"
    _description = "To add the products in sheet"
    _rec_name = "sheet_id"


    sequence = fields.Integer(string='Sequence')
    sheet_id = fields.Many2one('website.order.sheet',required=True,string="Sheet")
    user_id = fields.Many2one('res.users','User')
    new_sheet_id = fields.Many2one('website.order.sheet',string="Sheet")
    section = fields.Char(string='Section Name',required=True)
    product_ids = fields.Many2many('product.product',string='Products')
    line_product_ids = fields.One2many('section.product',"sheet_line_id",string='Section Products')


    @api.onchange('section')
    def user_section(self):
        self.user_id = self.sheet_id.user_id.id    

    def section_add_products(self):
        
        """
        Return 'add purchase history to so wizard'
        """
        view_id = self.env.ref('price_paper.view_purchase_history_add_so_wiz').id
        user_id = self.user_id
        # products = self.order_line.mapped('product_id').ids
        sales_history = self.env['sale.history'].search(
            ['|', ('active', '=', False), ('active', '=', True), ('partner_id', '=', user_id.partner_id.id),
              ('product_id', '!=', False)]).filtered(
            lambda r: not r.product_id.categ_id.is_storage_contract  and not r.product_id.id in self.product_ids.ids)
        # addons product filtering
        addons_products = sales_history.mapped('product_id').filtered(lambda rec: rec.need_sub_product).mapped('product_addons_list')
        if addons_products:
            sales_history = sales_history.filtered(lambda rec: rec.product_id not in addons_products)

        search_products = sales_history.mapped('product_id').ids
        context = {
            'default_sale_history_ids': [(6, 0, sales_history.ids)],
            'products': search_products
        }       
        
        return {
            'name': '%s # %s' % (user_id.partner_id.display_name, self.section ),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'add.purchase.history.so',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }

class LineProduct(models.Model):
    _name = 'section.product'
    _rec_name='product_id'
    
    sequence = fields.Integer(string='Sequence')
    sheet_line_id = fields.Many2one('order.sheet.lines',string='Order Sheet Line')
    product_id = fields.Many2one('product.product',string='Product')
    default_code = fields.Char(string='Internal Refernce',related='product_id.default_code')
    uom_id = fields.Many2one('uom.uom',string='uom')

