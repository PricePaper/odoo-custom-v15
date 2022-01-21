# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class inactive_customer_wizard(models.TransientModel):
    _name = 'inactive.customer.report.wizard'
    _description = 'Report Inactive Customer'

    latest_sale_date = fields.Date(string='Latest Sale Before')

    def display_inactive_customer_report(self):
        latest_sale_date = "%s 00:00:00" % (str(self.latest_sale_date))

        self._cr.execute(
            "select id from res_partner where id not in (select partner_id from sale_order where confirmation_date > '%s' and state in ('sale', 'done')) and customer='t' and supplier='f' and active='t'" % (
                latest_sale_date))

        par_ids = self._cr.fetchall()
        partner_ids = [par_id and par_id[0] for par_id in par_ids]

        action_id = self.env.ref('base.action_partner_form').read()[0]
        if action_id:
            return {
                'name': _('Inactive Customers Since %s' % (self.latest_sale_date)),
                'type': action_id['type'],
                'res_model': action_id['res_model'],
                'view_mode': 'tree,form',
                'search_view_id': action_id['search_view_id'],
                'domain': [["id", "in", partner_ids]],
                'help': action_id['help'],
                'context': {'search_default_customer': 1}
            }


inactive_customer_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
