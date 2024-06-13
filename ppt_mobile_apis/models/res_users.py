# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def action_reset_user_password(self, user_id):

        result = []
        message = {'success': False,
                   'error': False}

        if not isinstance(user_id, int):
            message['error'] = "user_id must be an integer"
            result.append(message)
            return result

        user = self.browse(user_id)

        if not user.exists():
            message['error'] = "User does not exist"
            result.append(message)
            return result

        try:
            user.action_reset_password()
            message['success'] = True
        except Exception as e:
            message['error'] = str(e)

        result.append(message)
        return result

