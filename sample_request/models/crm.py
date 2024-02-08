# -*- coding: utf-8 -*-

from odoo import fields,models,api,_

class CrmLead(models.Model):
    _inherit='crm.lead'


    def sample_request_action(self):
        self.ensure_one()
        return {
            'name': _('Sample Reuwar'),
            'view_mode': 'form',
            'res_model': 'sample.request',
            'domain': [('id', '=', self.sample_request_id.id)],
            'res_id': self.sample_request_id.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': {'default_type': self.type}
        }

    sample_request_id = fields.Many2one('sample.request',string='Sample Request')
