# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(
        selection_add=[('general', "general")], default='general',
        ondelete={'general': 'set default'})
    qr_generale = fields.Boolean(
        string="Enable QR generales", help="Enable the use of QR-generales when paying by general.")

    @api.depends('provider')
    def _compute_view_configuration_fields(self):
        """ Override of payment to hide the credentials page.

        :return: None
        """
        super()._compute_view_configuration_fields()
        self.filtered(lambda acq: acq.provider == 'general').write({
            'show_credentials_page': False,
            'show_payment_icon_ids': False,
            'show_pre_msg': False,
            'show_done_msg': False,
            'show_cancel_msg': False,
        })

    @api.model_create_multi
    def create(self, values_list):
        """ Make sure to have a pending_msg set. """
        # This is done here and not in a default to have access to all required values.
        acquirers = super().create(values_list)
        acquirers._general_ensure_pending_msg_is_set()
        return acquirers

    def write(self, values):
        """ Make sure to have a pending_msg set. """
        # This is done here and not in a default to have access to all required values.
        res = super().write(values)
        self._general_ensure_pending_msg_is_set()
        return res

    def _general_ensure_pending_msg_is_set(self):
        for acquirer in self.filtered(lambda a: a.provider == 'general' and not a.pending_msg):
            company_id = acquirer.company_id.id
            # filter only bank accounts marked as visible
            accounts = self.env['account.journal'].search([
                ('type', '=', 'cash'), ('company_id', '=', company_id)
            ]).bank_account_id
            acquirer.pending_msg = f'''<div>
                <h3>{_("Please make the payment at the time of delivery")}</h3>
                <h4>{_("Communication")}</h4>
                <p>{_("Please use the order name as communication reference.")}</p>
                </div>'''
