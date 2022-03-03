# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class inactive_product_wizard(models.TransientModel):
    _name = 'inactive.product.report.wizard'
    _description = 'Report Inactive Product'

    latest_sale_date = fields.Date(string='Latest Sale Before')

    def display_inactive_product_report(self):
        latest_sale_date = "%s 00:00:00" % (str(self.latest_sale_date))

        self.env.cr.execute(
            "select sol.product_id from sale_order_line sol join sale_order so ON (so.id = sol.order_id) where so.date_order > '%s' and so.state in ('sale', 'done')" % (
                latest_sale_date))

        pro_ids = self._cr.fetchall()

        product_ids = [pro_id and pro_id[0] for pro_id in pro_ids]
        products = self.env['product.product'].search([('sale_ok', '=', True),
            ('type', '!=', 'service')]).filtered(lambda r : r.id not in product_ids)

        action_id = self.env.ref('product.product_normal_action_sell').read()[0]
        if action_id:
            return {
                'name': _('Inactive Products Since %s' % (self.latest_sale_date)),
                'type': action_id['type'],
                'res_model': action_id['res_model'],
                'view_mode': 'tree,form',
                'search_view_id': action_id['search_view_id'],
                'domain': [["id", "in", products.ids]],
                'help': action_id['help'],
            }


inactive_product_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
