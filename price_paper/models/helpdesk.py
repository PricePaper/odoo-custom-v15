# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class HelpDeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    is_sales_team = fields.Boolean(string='Sales Team')
    is_credit_team = fields.Boolean(string='Credit Team')


class HelpDeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    def assign_ticket_to_self(self):
        self.ensure_one()
        if self.user_id and self.user_id != self.env.user:
            raise UserError('Ticket already assigned to %s' % self.user_id.name)
        super(HelpDeskTicket, self).assign_ticket_to_self()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
