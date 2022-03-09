# -*- coding: utf-8 -*-

from odoo import models, api


class ProductProduct(models.Model):
    _inherit = 'product.product'


    def name_get(self):
        """
        overidden to show name of product as only the sku
        in the sale line report view (only there)
        """
        result = []
        #sale_line_view_action = self.env.ref('sale_line_reports.action_sale_line_reports_price_paper')
        if self.env.context.get('custom_search'):
            for record in self:
                name = record.default_code
                result.append((record.id, name))
        else:
            result = super(ProductProduct, self).name_get()
        return result


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
