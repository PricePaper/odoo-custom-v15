# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def _get_default_purchase_msg(self):
        result = """
            <div style = "font-family: 'Gotham Bold', sans-serif;font-size:14px;" >
                <p>Purchase Orders must be confirmed via e-mail or phone. Delivery appointments are required. Receiving hours are from M-F between 6 AM and 2 PM, excluding holidays.
                <span>POs are valid up to 30 days from the wanted date. Shipments must be unloaded to dock and are pallet exchange, only.</span>
                Print over-runs of more than 10% will not be accepted. Thank you.</p>
            </div>"""
        return result

    purchase_writeoff_account_id = fields.Many2one('account.account', string='Purchase Writeoff Account',
                                                   domain=[('deprecated', '=', False)])
    purchase_default_message = fields.Html(string='Default Purchase Message', default=_get_default_purchase_msg)


ResCompany()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
