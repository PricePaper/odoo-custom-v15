# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleWarningWizard(models.TransientModel):
    _name = 'sale.warning.wizard'
    _description = 'Sales Warning Wizard'

    warning_message = fields.Text(string='Warning')

    def close_window(self):
        return True
        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'reload',
        # }


SaleWarningWizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
