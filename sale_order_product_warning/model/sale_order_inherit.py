from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    product_status = fields.Boolean()


    #check status Of Order line
    @api.onchange('order_line')
    def _onchange_order_line(self):
        product_list=[]
        check_duplicate = 0
        for line in self.order_line:
            if line.product_id.id in product_list:
                check_duplicate+=1

            product_list.append(line.product_id.id)
        if check_duplicate>0:
            self.product_status=True
        else:
            self.product_status=False

    #Update vlaue of product status field because we mark as true in onchange        
    def write(self, vals):
        vals['product_status']=False
        res = super(SaleOrder, self).write(vals)
        return res

    #Update vlaue of product status field because we mark as true in onchange 
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['product_status']=False
        res = super(SaleOrder, self).create(vals_list)
        return res