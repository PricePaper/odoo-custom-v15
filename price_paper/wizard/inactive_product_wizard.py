# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class InactiveProductWizard(models.TransientModel):
    _name = 'inactive.product.report.wizard'
    _description = 'Report Inactive Product'

    latest_sale_date = fields.Date(string='Latest Sale Before')

    def display_inactive_product_report(self):
        latest_sale_date = "%s 00:00:00" % (str(self.latest_sale_date))

        self.env.cr.execute("""select sol.product_id from sale_order_line sol 
        join sale_order so ON (so.id = sol.order_id) 
        where so.date_order > '%s' and so.state in ('sale', 'done')""" % (latest_sale_date))

        pro_ids = self._cr.fetchall()

        product_ids = [pro_id and pro_id[0] for pro_id in pro_ids]
        products = self.env['product.product'].search([('sale_ok', '=', True), ('type', '!=', 'service'), ('id', 'not in', product_ids)])
            # .filtered(lambda r : r.id not in product_ids)

        action = self.env.ref('product.product_normal_action_sell').read()[0]
        if action:
            action.update({
                'name': 'Inactive Products Since %s' % self.latest_sale_date,
                'domain': [["id", "in", products.ids]],
            })
            return action


InactiveProductWizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
