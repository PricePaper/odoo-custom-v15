# -*- coding: utf-8 -*-

from odoo import models, fields, api


class BatchWarningWizard(models.TransientModel):
    _name = 'batch.warning.wizard'
    _description = 'Batch Warning Wizard'

    warning_message = fields.Text(string='Warning')

    def close_window(self):
        return True


BatchWarningWizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
