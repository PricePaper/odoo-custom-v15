# -*- coding: utf-8 -*-

from odoo import api, models, fields
import json


class PushToken(models.Model):
    _name = 'push.token'
    _description = 'Mobile App push notification tokens'

    partner_id = fields.Many2one('res.partner', string="Partner", required=True)
    user_id = fields.Many2one('res.users', string="Related User", required=True)
    device_token = fields.Char(string="Token")






class PushNotification(models.Model):
    _name = 'push.notification'
    _description = 'Mobile App push notifications'

    partner_id = fields.Many2one('res.partner', string="Partner", required=True)
    res_model = fields.Char(string="Res Model")
    res_id = fields.Integer(string="Res ID")
    event_name = fields.Selection([('order_confirm', 'Sale Order Confirmation')], string="Event Name")
    event_description = fields.Char(string="Event Description")
    state = fields.Selection([('draft', 'Draft'), ('fetched', 'Fetched'), ('failed', 'Failed')])




    @api.model
    def trigger_order_confirmation(self, order_id):
        """
        to test push notifications
        @param order_id: sale order
        @return:
        """
        order_id = self.env['sale.order'].browse(order_id)
        vals = {
            'partner_id': order_id.partner_id.id,
            'res_model': order_id._name,
            'res_id': order_id.id,
            'event_name': 'order_confirm',
            'event_description': 'Your order has been confirmed',
            'state': 'draft'
        }
        rec = self.create(vals)
        return json.dumps(True if rec else False)
