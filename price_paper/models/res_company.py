# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    burden_percent = fields.Float(string='Burden %')
    partner_delivery_method_id = fields.Many2one('delivery.carrier', string='Delivery Method')
    partner_country_id = fields.Many2one('res.country', string=' Partner\'s Country')
    partner_state_id = fields.Many2one('res.country.state', string='State')
    price_lock_days = fields.Integer(string='Price list lock days #', default=90)
    sale_history_months = fields.Integer(string='Sales History Months ', default=15)
    standard_price_config_days = fields.Integer(string='Standard price lock # days', default=60)
    credit_limit = fields.Integer(string='Credit Limit', default=4000)
    storage_product_id = fields.Many2one('product.product', string='Storage Product')
    discount_account_id = fields.Many2one('account.account', domain=[('deprecated', '=', False)])

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    check_printing_journal_id = fields.Many2one('account.journal',
        string='Journal for check printing',
        config_parameter='price_paper.check_printing_journal_id')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
