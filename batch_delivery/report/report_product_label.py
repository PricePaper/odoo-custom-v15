# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError


class ReportBatchProductLabel(models.AbstractModel):

    _name = "report.batch_delivery.report_batch_product_label"
    _description = 'Batch Product Label Report'

    def _get_product_labels(self, docs):
        picking_ids = self.env['stock.picking']
        for doc in docs:
            picking_ids += doc.picking_ids
        ordered_product_label = self.get_ordered_product_label(picking_ids)
        return ordered_product_label

    def get_ordered_product_label(self, pickings):

        picking_list = []
        for picking in pickings.sorted('sequence'):
            location_main = {}
            for line in picking.move_lines:
                location = line.product_id.property_stock_location and line.product_id.property_stock_location.name or '00-Location not assigned'

                order = line.sale_line_id.order_id
                sections = order.order_line.filtered(lambda rec: rec.display_type == 'line_section'
                        and rec.sequence < line.sale_line_id.sequence).sorted(key=lambda b: b.sequence,reverse = True)
                section = sections and sections[0] or False

                if location_main.get(location, False):
                    location_main.get(location, False).append((line, section))
                else:
                    location_main.update({location: [(line, section)]})

            locations = location_main.keys()
            location_list = []
            for location in sorted(locations):
                location_list.append((location, location_main[location]))

            picking_list.append(location_list)
        return picking_list


    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.picking.batch'].browse(docids)
        if not docs.mapped('picking_ids'):
            raise UserError(_('Nothing to print.'))
        return {'doc_ids': docs.ids,
                'doc_model': 'stock.picking.batch',
                'docs': docs,
                'data': data,
                'get_product_labels': self._get_product_labels,
            }


class ReportpickingProductLabel(models.AbstractModel):

    _name = "report.batch_delivery.report_product_label"
    _description = 'Product Label Report'

    def _get_product_labels(self, docs):
        picking_ids = self.env['stock.picking']
        for doc in docs:
            picking_ids += doc
        ordered_product_label = self.env['report.batch_delivery.report_batch_product_label'].get_ordered_product_label(picking_ids)
        return ordered_product_label

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.picking'].browse(docids)
        if not docs:
            raise UserError(_('Nothing to print.'))
        return {'doc_ids': docs.ids,
                'doc_model': 'stock.picking',
                'docs': docs,
                'data': data,
                'get_product_labels': self._get_product_labels,
            }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
