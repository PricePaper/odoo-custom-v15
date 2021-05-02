# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError

class ReportMasterPickingTicket(models.AbstractModel):

    _name = "report.batch_delivery.master_pick_ticket_report"
    _description = 'Master Pick Ticket Report'

    def _get_master_tickets(self, docs):
        picking_ids = self.env['stock.picking']
        for doc in docs:
            if doc.late_order_print:
                picking_ids += doc.picking_ids.filtered(lambda rec: rec.is_late_order)
            else:
                picking_ids += doc.picking_ids
        product_main = {}
        for picking in picking_ids.filtered(lambda rec: rec.state != 'cancel'):
            for line in picking.move_line_ids:
                location = line.product_id.property_stock_location and line.product_id.property_stock_location.name or '00-Location not assigned'
                if product_main.get(location, False):
                    if product_main.get(location, False).get(line.product_id, False):
                        if line.product_uom_id in  product_main.get(location, False).get(line.product_id, False):
                            product_main.get(location, False).get(line.product_id, False)[line.product_uom_id] = product_main.get(location, False).get(line.product_id, False).get(line.product_uom_id, 0)+line.qty_done
                        else:
                            product_main.get(location, False).get(line.product_id, False)[line.product_uom_id] = line.qty_done
                    else:
                        product_main.get(location, False)[line.product_id] = {line.product_uom_id:line.qty_done}
                else:
                    product_main.update({location: {line.product_id:{line.product_uom_id:line.qty_done}}})
        locations = product_main.keys()
        location_list = []
        for location in sorted(locations):
            location_list.append((location, product_main[location]))
        return location_list

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.picking.batch'].browse(docids)
        if not docs.mapped('picking_ids'):
            raise UserError(_('Nothing to print.'))
        return {'doc_ids': docs.ids,
                'doc_model': 'stock.picking.batch',
                'docs': docs,
                'data': data,
                'get_master_tickets': self._get_master_tickets,
            }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
