# -*- coding: utf-8 -*-

from odoo import models, api, fields
import logging as server_log

class CostChangeParent(models.Model):
    _inherit = 'cost.change.parent'

    is_mail_sent = fields.Boolean('Mail sent', copy=False, default=False)

    @api.model
    def cost_change_mail_cron(self):

        email_to = self.env['ir.config_parameter'].sudo().get_param('price_maintanance.cost_change_email_ids')
        if not email_to:
            server_log.error('Cost change mail : receiver email is not configured.')
        records = self.env['cost.change.parent'].search([('is_mail_sent', '!=', True), ('is_done', '=', 'True')])
        if records:
            mail_template = self.env.ref('price_maintanance.email_template_cost_change')
            mail_template.with_context(email_from=self.env.company.email, email_to=email_to, records=records).send_mail(self.id,
                                                                                                       force_send=True)
            records.write({'is_mail_sent': True})
        return True

class CostChange(models.Model):
    _inherit = 'cost.change'

    @api.model
    def default_get(self, fields_list):
        res = super(CostChange, self).default_get(fields_list)
        if self._context.get('product_id', False):
            res['product_id'] = self._context.get('product_id')
        return res

class CostChangeMailReport(models.AbstractModel):
    _name = 'report.price_maintanance.report_cost_change'
    _description = 'Cost change mail report'

    @api.model
    def _get_report_values(self, docids, data=None):

        docs = self.env['cost.change.parent'].search([('is_mail_sent', '!=', True), ('is_done', '=', 'True')])
        if self._context.get('records'):
            docs = self._context.get('records')
        return {
            'docs': docs,
        }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
