# -*- coding: utf-8 -*-

from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mobile_app_sale_team = fields.Many2one('crm.team',
        string='Mobile App Sale Team',
        config_parameter='ppt_mobile_apis.mobile_app_sale_team')
    mobile_app_new_category = fields.Many2one('product.public.category',
        string='Mobile App New Arrival category',
        config_parameter='ppt_mobile_apis.mobile_app_new_category')
    cod_payment_term = fields.Many2one('account.payment.term',string='COD',config_parameter='ppt_mobile_apis.cod_payment_term')
    ach_payment_term = fields.Many2one('account.payment.term',string='ACH',config_parameter='ppt_mobile_apis.ach_payment_term')
    card_payment_term = fields.Many2one('account.payment.term',string='CARD',config_parameter='ppt_mobile_apis.card_payment_term')
    credit_payment_term = fields.Many2one('account.payment.term',string='CREDIT',config_parameter='ppt_mobile_apis.credit_payment_term')
