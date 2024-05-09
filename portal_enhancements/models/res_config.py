from odoo import fields, models, api, _
from odoo.exceptions import UserError

class Website(models.Model):
    _inherit='website'
    helpdesk_team_website = fields.Many2one('helpdesk.team')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    helpdesk_team_website = fields.Many2one('helpdesk.team', related='website_id.helpdesk_team_website', readonly=False)
    resale_document_id_sign = fields.Many2one('sign.template',string="Resale Document",config_parameter='portal_enhancements.resale_document_id_sign')
    ach_debit_form = fields.Many2one('sign.template',string="Ach Debit Form",config_parameter='portal_enhancements.ach_debit_form')
    credit_application = fields.Many2one('sign.template',string="Credit Application Template",config_parameter='portal_enhancements.credit_application')
    cod_payment_terms = fields.Many2one('account.payment.term',string='Cod Payment Terms for New customer',config_parameter='portal_enhancements.cod_payment_terms')
    helpdesk_team_onbaording = fields.Many2one('helpdesk.team',string='Helpdesk Team to handle Onboarding',config_parameter='portal_enhancements.helpdesk_team_onbaording')
