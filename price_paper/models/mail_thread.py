from odoo import models, fields, api,_
import logging

class MailThread(models.AbstractModel):
    _inherit = ['mail.thread']

    @api.multi
    def create(self, vals):
        vals.pop('message_follower_ids', False)
        return super().create(vals)
