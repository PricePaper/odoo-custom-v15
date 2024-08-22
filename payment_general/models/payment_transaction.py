# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import _, api, models
from odoo.exceptions import ValidationError

from odoo.addons.payment_general.controllers.main import generalController

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return general-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of acquirer-specific processing values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider != 'general':
            return res

        return {
            'api_url': generalController._accept_url,
            'reference': self.reference,
        }

    @api.model
    def _get_tx_from_feedback_data(self, provider, data):
        """ Override of payment to find the transaction based on general data.

        :param str provider: The provider of the acquirer that handled the transaction
        :param dict data: The general feedback data
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_feedback_data(provider, data)
        if provider != 'general':
            return tx

        reference = data.get('reference')
        tx = self.search([('reference', '=', reference), ('provider', '=', 'general')])
        if not tx:
            raise ValidationError(
                "Wire general: " + _("No transaction found matching reference %s.", reference)
            )
        return tx

    def _process_feedback_data(self, data):
        """ Override of payment to process the transaction based on general data.

        Note: self.ensure_one()

        :param dict data: The general feedback data
        :return: None
        """
        
        super()._process_feedback_data(data)
        if self.provider != 'general':
            return

        _logger.info(
            "validated general payment for tx with reference %s: set as pending", self.reference
        )
        if self.sale_order_ids:
            for rec in self.sale_order_ids:
                rec.invoice_address_id = rec.partner_id.id
                if rec.partner_id.property_payment_term_id:
                    rec.payment_term_id = rec.partner_id.property_payment_term_id.id
                rec.action_confirm()
        self._set_pending()

    def _log_received_message(self):
        """ Override of payment to remove general acquirer from the recordset.

        :return: None
        """
        other_provider_txs = self.filtered(lambda t: t.provider != 'general')
        super(PaymentTransaction, other_provider_txs)._log_received_message()

    def _get_sent_message(self):
        """ Override of payment to return a different message.

        :return: The 'transaction sent' message
        :rtype: str
        """
        message = super()._get_sent_message()
        if self.provider == 'general':
            message = _(
                "The customer has selected %(acq_name)s to make the payment.",
                acq_name=self.acquirer_id.name
            )
        return message
