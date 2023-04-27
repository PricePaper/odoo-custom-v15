from odoo.addons.website_sale.controllers import main
from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.fields import Command
from odoo.http import request
from werkzeug.exceptions import Forbidden, NotFound
import logging 
_logger = logging.getLogger(__name__)

class WebsiteSale(main.WebsiteSale):

    @http.route('/save/sheet',type='json',auth="user",website=True,csrf=False)
    def save_sheet(self,sheet_data,new_data=False):
        user = request.env.user
        for key,val in sheet_data.items():
            
            section_id = int(key)
            section = request.env['order.sheet.lines'].sudo().browse([int(section_id)])
            section.line_product_ids = False
            product_ids = list(map(int,val['product_ids']))
            section.write({
                'section':val['name'],
                'line_product_ids':[(0,0,{"product_id":product})for product in product_ids]
            })
        _logger.info(f"+============={new_data}")
        if new_data:
            data_list = [(0,0,{'section':rec['section'],'line_product_ids':[(0,0,{"product_id":product})for product in rec['product_ids']]} ) for rec in new_data]
            order_sheet = request.env['website.order.sheet'].search([('user_id','=',user.id)],limit=1)
            order_sheet.order_lines = data_list
        return({'result':True})


    @http.route(['/sheet/add/prod'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def order_history_table_add(self, section_key,prod_ids):
        sheet_line = request.env['order.sheet.lines'].sudo().browse([int(section_key)])
        old_prod = sheet_line.product_ids.ids
        prod_ids = list(map(int,prod_ids))
        prod_ids.extend(old_prod)
        sheet_line.product_ids = [(6,0,prod_ids)]
        # sheet_line = request.env['order.sheet.lines'].sudo().browse([int(section_key)])
        # old_prod = sheet_line.product_ids.ids
        prod_ids = list(map(int,prod_ids))
        # prod_ids.extend(old_prod)
        # sheet_line.product_ids = [(6,0,prod_ids)]
        product_ids = request.env['product.product'].sudo().browse(prod_ids)
        value={}
        value['prod_li'] = request.env['ir.ui.view']._render_template("website_order_sheet.prod_li", {
            'product_ids':product_ids,'line_id':int(section_key)
        })
        return value
        # return True



    @http.route(['/sheet/browse/set'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def order_history_table(self, offset):
        user = request.env.user
        sheet_id = request.env['website.order.sheet'].sudo().search([('user_id','=',user.id)],limit=1)


        # products = self.order_line.mapped('product_id').ids
        sales_history = request.env['sale.history'].sudo().search(
            ['|', ('active', '=', False), ('active', '=', True), ('partner_id', '=', user.partner_id.id),
              ('product_id', '!=', False),('product_id.categ_id.is_storage_contract','=',False)],limit=15,offset=int(offset))
        # addons product filtering
        addons_products = sales_history.mapped('product_id').filtered(lambda rec: rec.need_sub_product).mapped('product_addons_list')
        if addons_products:
            sales_history = sales_history.filtered(lambda rec: rec.product_id not in addons_products)

        search_products = sales_history.mapped('product_id').ids
        value={}
        value['history_table'] = request.env['ir.ui.view']._render_template("website_order_sheet.history_table", {
            'sale_history':sales_history,'total':len(sales_history),'offset':int(offset)
        })
        return value


    @http.route(['/order/sheet'], type='http', auth="user", methods=['get'], website=True, csrf=False)
    def order_sheet(self):
        user = request.env.user
        sheet_id = request.env['website.order.sheet'].sudo().search([('user_id','=',user.id)],limit=1)
        
        # products = self.order_line.mapped('product_id').ids
        sales_history = request.env['sale.history'].sudo().search(
            ['|', ('active', '=', False), ('active', '=', True), ('partner_id', '=', user.partner_id.id),
              ('product_id', '!=', False),('product_id.categ_id.is_storage_contract','=',False)],limit=15,offset=0)
        # addons product filtering
        addons_products = sales_history.mapped('product_id').filtered(lambda rec: rec.need_sub_product).mapped('product_addons_list')
        if addons_products:
            sales_history = sales_history.filtered(lambda rec: rec.product_id not in addons_products)

        search_products = sales_history.mapped('product_id').ids
        context = {
            'default_sale_history_ids': [(6, 0, sales_history.ids)],
            'products': search_products
        }  
        # import pdb
        # pdb.set_trace()

        return request.render('website_order_sheet.user_sheet',{'sheet':sheet_id,'sale_history':sales_history,'total':len(sales_history),'offset':0})