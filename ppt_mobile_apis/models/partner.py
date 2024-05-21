# -*- coding: utf-8 -*-

from odoo import api, models, fields


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def get_partner_payment_methods(self, partner_id=None):

        result = []

        if partner_id is None or not isinstance(partner_id, int):
            return result

        partner = self.browse(partner_id)
        if partner:

            default_payment_term = partner.property_payment_term_id

            if default_payment_term:
                payment_terms = {
                    'payment_term': default_payment_term.name,
                    'payment_term_id':default_payment_term.id,
                    'payment_methods': []
                }

                if default_payment_term.payment_method == 'ach-debit':
                    payment_terms['payment_methods'] = [
                        {'name': 'Credit Card', 'availability': False, 'default': False},
                        {'name': 'COD', 'availability': False, 'default': False},
                        {'name': 'ACH-Debit', 'availability': True, 'default': True}
                    ]
                elif default_payment_term.is_pre_payment:
                    payment_terms['payment_methods'] = [
                        {'name': 'Credit Card', 'availability': True, 'default': True},
                        {'name': 'COD', 'availability': False, 'default': False},
                        {'name': 'ACH-Debit', 'availability': True, 'default': False}
                    ]
                elif default_payment_term.is_discount:
                    payment_terms['payment_methods'] = [
                        {'name': 'Credit Card', 'availability': True, 'default': False},
                        {'name': 'COD', 'availability': True, 'default': True},
                        {'name': 'ACH-Debit', 'availability': False, 'default': False}
                    ]

                result.append(payment_terms)

            return result
