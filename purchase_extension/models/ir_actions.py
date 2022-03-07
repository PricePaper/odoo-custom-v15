# -*- coding: utf-8 -*-

from odoo import models

class IrActionsXlsxReportDownload(models.AbstractModel):

    _name = 'ir_actions_xlsx_download'
    _description = 'Technical model for report downloads'

    def _get_readable_fields(self):
        return self.env['ir.actions.actions']._get_readable_fields() | {'data'}
