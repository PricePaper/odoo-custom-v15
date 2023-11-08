# -*- coding: utf-8 -*-

from odoo import fields, models, _


class VendorProductLines(models.TransientModel):
    _inherit = 'vedor.product.lines'

    product_uom = fields.Many2one('uom.uom', related='product_id.ppt_uom_id', string="UOM")

class VendorProductReportWizard(models.TransientModel):
    _inherit = 'vedor.product.report.wizard'

    def calculate_result_dict(self, result):
        out_lines = {}
        for result_line in result:
            product = self.env['product.product'].browse(result_line[0])
            if product.ppt_uom_id.id == result_line[3]:
                if product in out_lines:
                    out_lines[product]['ordered_qty'] = out_lines[product]['ordered_qty'] + result_line[1]
                    out_lines[product]['delivered_qty'] = out_lines[product]['delivered_qty'] + result_line[2]
                else:
                    out_lines[product] = {'ordered_qty': result_line[1], 'delivered_qty': result_line[2]}

            else:
                uom = self.env['uom.uom'].browse(result_line[3])
                ordered_qty = uom._compute_quantity(result_line[1], product.ppt_uom_id)
                delivered_qty = uom._compute_quantity(result_line[2], product.ppt_uom_id)
                if product in out_lines:
                    out_lines[product]['ordered_qty'] = out_lines[product]['ordered_qty'] + ordered_qty
                    out_lines[product]['delivered_qty'] = out_lines[product]['delivered_qty'] + delivered_qty
                else:
                    out_lines[product] = {'ordered_qty': ordered_qty, 'delivered_qty': delivered_qty}
        return out_lines
