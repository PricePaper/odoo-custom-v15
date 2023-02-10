# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def _get_default_sale_msg(self):
        result = """
            <div style = "font-family: 'Gotham Bold', sans-serif;font-size:13px;" >
                <p>
                </p>
            </div>"""
        return result

    driver_writeoff_account_id = fields.Many2one('account.account', string='Driver writeoff account')
    sale_default_message = fields.Html(string='Default Purchase Message', default=_get_default_sale_msg)


ResCompany()
