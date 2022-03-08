# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class InactiveCustomerWizard(models.TransientModel):
    _name = 'inactive.customer.report.wizard'
    _description = 'Report Inactive Customer'

    latest_sale_date = fields.Date(string='Latest Sale Before')

    def display_inactive_customer_report(self):
        latest_sale_date = "%s 00:00:00" % (str(self.latest_sale_date))

        self._cr.execute("""select id from res_partner where id not in 
        (select partner_id from sale_order where date_order > '%s' and state in ('sale', 'done'))
         and customer is true and supplier is not true and active is true""" % (latest_sale_date))

        par_ids = self._cr.fetchall()
        partner_ids = [par_id and par_id[0] for par_id in par_ids]

        action = self.sudo.env.ref('account.res_partner_action_customer').read()[0]
        if action:
            action.update({
                'domain': [["id", "in", partner_ids]],
                'name': 'Inactive Customers Since %s' % self.latest_sale_date,
            })
            return action


InactiveCustomerWizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
