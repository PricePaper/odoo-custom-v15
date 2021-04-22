# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError


class ReportPickingBatch(models.AbstractModel):

    _name = "report.batch_delivery.report_batch_picking_all"
    _description = 'Batch Picking Report (All)'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.picking.batch'].browse(docids)
        if not docs.mapped('picking_ids'):
            raise UserError(_('Nothing to print.'))
        return {'doc_ids': docs.ids,
                'doc_model': 'stock.picking.batch',
                'docs': docs,
                'data': data
            }


class ReportActivePickingBatch(models.AbstractModel):

    _name = "report.batch_delivery.report_batch_picking_active"
    _description = 'Batch Picking Report (Active)'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.picking'].browse(docids)
        if not docs:
            raise UserError(_('Nothing to print.'))
        return {'doc_ids': docs.ids,
                'doc_model': 'stock.picking',
                'docs': docs,
                'data': data,
            }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
