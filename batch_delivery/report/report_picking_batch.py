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

class ReportActiveInvoiceWithOutPayment(models.AbstractModel):

    _name = "report.batch_delivery.report_ppt_selected_invoice_standard"
    _description = 'Invoice Report With Out Payment (Active)'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.move'].browse(docids)
        if not docs:
            raise UserError(_('Nothing to print.'))
        for invoice in docs:
            if invoice.picking_ids:
                drivers = invoice.picking_ids.mapped('batch_id.truck_driver_id')
                if drivers and not all([d.firstname for d in drivers]):
                    raise UserError(_('Missing firstname from driver: %s' % '\n'.join(
                        [d.name for d in drivers if not d.firstname])))
        return {'doc_ids': docs.ids,
                'doc_model': 'move',
                'docs': docs,
                'data': data,
                }



class ReportActiveInvoiceWithPayment(models.AbstractModel):

    _name = "report.batch_delivery.report_ppt_selected_invoice_with_payment"
    _description = 'Invoice WithPayment Report (Active)'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.move'].browse(docids)
        if not docs:
            raise UserError(_('Nothing to print.'))
        for invoice in docs:
            if invoice.picking_ids:
                drivers = invoice.picking_ids.mapped('batch_id.truck_driver_id')
                if drivers and not all([d.firstname for d in drivers]):
                    raise UserError(_('Missing firstname from driver: %s' % '\n'.join([d.name for d in drivers if not d.firstname])))
        return {'doc_ids': docs.ids,
                'doc_model': 'account.move',
                'docs': docs,
                'data': data,
            }

# # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
