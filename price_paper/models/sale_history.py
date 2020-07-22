# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.addons.queue_job.job import job

class SaleOrderHistory(models.Model):
    _name = 'sale.history'
    _description = 'Sale History'

    partner_id = fields.Many2one('res.partner', string='Customer')
    product_id = fields.Many2one('product.product', related='order_line_id.product_id', string='Product')
    uom_id = fields.Many2one('uom.uom', related='order_line_id.product_uom', string='UOM')
    order_id = fields.Many2one('sale.order' ,related='order_line_id.order_id', string='Order')
    order_line_id = fields.Many2one('sale.order.line', string='Order')
    active = fields.Boolean('Active', default=True, track_visibility=True)


    @api.multi
    @job
    def job_queue_create_purchase_history(self, line):
        """
        Queue Job
        create sale history if there is no archived history.
        Modify sale history if there is existing archived history.
        """
        archived_id = self.env['sale.history'].search([('active', '=', False),('partner_id', '=', line[3]),('product_id', '=', line[1]), ('uom_id', '=', line[2])], limit=1)
        if archived_id:
            vals={'order_line_id' : line[0]}
            archived_id.write(vals)
        else:
            vals={'order_line_id' : line[0], 'partner_id' : line[3], 'active': True}
            self.env['sale.history'].create(vals)
        return True

    @api.model
    def update_purchase_history(self):
        """
        Cron job to create or modify sale history
        Delete active sale history and recreate it,
        modify archived sale history
        """

        self.env['sale.history'].search([]).unlink()
        self._cr.execute("select distinct on (so.partner_id,sol.product_id, sol.product_uom) sol.id,sol.product_id,sol.product_uom,so.partner_id  from sale_order_line sol join sale_order so on sol.order_id = so.id where so.state in ('done', 'sale') order by so.partner_id, sol.product_id, sol.product_uom, so.confirmation_date desc")
        line_ids = self._cr.fetchall()
        for line in line_ids:
            self.with_delay(channel='root.Sale History').job_queue_create_purchase_history(line)


SaleOrderHistory()
