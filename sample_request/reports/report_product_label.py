# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError

class ReportSampleProductLabel(models.AbstractModel):

    _name = "report.sample_request.report_sample_product_label"
    _description = 'Product Label Report'

    def get_ordered_product_label(self, pickings):

        picking_list = []
        for picking in pickings:
            location_main = {}
            for line in picking.request_lines.filtered(lambda r: not r.is_reject):
                location = line.product_id.property_stock_location and line.product_id.property_stock_location.name or '00-Location not assigned'

                if location_main.get(location, False):
                    location_main.get(location, False).append(line)
                else:
                    location_main.update({location: [line]})

            locations = location_main.keys()
            location_list = []
            for location in sorted(locations):
                location_list.append((location, location_main[location]))

            picking_list.append(location_list)
        return picking_list

    def _get_product_labels(self, docs):
        req_ids = self.env['sample.request']
        for doc in docs:
            req_ids += doc
        return self.get_ordered_product_label(req_ids)

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sample.request'].browse(docids)
        if not docs:
            raise UserError(_('Nothing to print.'))
        return {'doc_ids': docs.ids,
                'doc_model': 'sample.request',
                'docs': docs,
                'data': data,
                'get_product_labels': self._get_product_labels,
            }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
