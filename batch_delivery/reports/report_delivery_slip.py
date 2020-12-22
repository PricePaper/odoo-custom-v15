# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError


class ReportBatchDeliverySlip(models.AbstractModel):

    _name = "report.batch_delivery.report_batch_delivery_slip"
    _description = 'Batch Delivery slip Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.picking.batch'].browse(docids)
        if not docs.mapped('picking_ids'):
            raise UserError(_('Nothing to print.'))
        return {'doc_ids': docs.ids,
                'doc_model': 'stock.picking.batch',
                'docs': docs,
                'data': data,
            }


ReportBatchDeliverySlip()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
