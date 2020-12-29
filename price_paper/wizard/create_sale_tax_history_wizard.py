# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.addons.queue_job.job import job


class SaleTaxHistoryWizard(models.TransientModel):
    _name = 'sale.tax.history.wizard'
    _description = 'Sales Tax History Wizard'

    @api.multi
    @job
    def job_queue_create_sale_tax_history(self, line):
        line = self.env['sale.order.line'].browse(line[0])
        tax = False
        if line.tax_id:
            tax = True
        vals = {'product_id': line.product_id.id, 'partner_id': line.order_id.partner_shipping_id.id, 'tax': tax}
        self.env['sale.tax.history'].create(vals)
        return True

    @api.multi
    def add_sale_tax_history_lines(self):
        """
        Creating sale tax history
        """
        self.env['sale.tax.history'].search([]).unlink()
        self._cr.execute(
            "select distinct on (so.partner_shipping_id,sol.product_id) sol.id  from sale_order_line sol join sale_order so on sol.order_id = so.id where so.state in ('done', 'sale') order by so.partner_shipping_id, sol.product_id, so.confirmation_date desc")
        line_ids = self._cr.fetchall()
        for line in line_ids:
            self.with_delay(channel='root.Sales_Tax_History').job_queue_create_sale_tax_history(line)


SaleTaxHistoryWizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
