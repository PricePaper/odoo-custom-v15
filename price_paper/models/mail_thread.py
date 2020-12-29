# -*- coding: utf-8 -*-

from odoo import models, api


class MailThread(models.AbstractModel):
    _inherit = ['mail.thread']

    @api.model
    def create(self, vals):
        if self._name == 'sale.order':
            vals.pop('message_follower_ids', False)
        return super().create(vals)


MailThread()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
