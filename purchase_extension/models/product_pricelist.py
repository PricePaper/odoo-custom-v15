# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import json
import io
from odoo.tools import date_utils
from datetime import datetime

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'


    def print_xlxs(self):
        data = {'rec': self.id}
        return {
                'type': 'ir_actions_xlsx_download',
                'data': {'model': 'product.pricelist',
                         'options': json.dumps(data, default=date_utils.json_default),
                         'output_format': 'xlsx',
                         'report_name': 'Excel Report',
                         }
                }


    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        rec = self.env['product.pricelist'].browse(data['rec'])
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        sheet.set_column(0, 0, 20)
        sheet.set_column(1, 1, 60)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 3, 15)
        cell_format = workbook.add_format({'font_size': '12px'})
        head = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'font_size': '10px'})
        row, col = 0, 0
        sheet.write(row, col, rec.name, cell_format)
        row += 1
        sheet.write(row, col, 'Date Prepared', cell_format)
        col += 1
        sheet.write(row, col, datetime.now().strftime("%m/%d/%Y"), cell_format)
        row += 1
        col = 0
        sheet.write(row, col, 'Valid Until', cell_format)
        col += 1
        if rec.expiry_date:
            sheet.write(row, col, rec.expiry_date.strftime("%m/%d/%Y"), cell_format)
        row += 1
        col = 0
        sheet.write(row, col, 'Partner', cell_format)
        col += 1
        names = ','.join([str(s.name) for s in rec.partner_ids])
        sheet.write(row, col, names, cell_format)

        row += 2
        col = 0
        sheet.write(row, col, 'Product Code', cell_format)
        col += 1
        sheet.write(row, col, 'Product Name', cell_format)
        col += 1
        sheet.write(row, col, 'UOM', cell_format)
        col += 1
        sheet.write(row, col, 'Price', cell_format)
        col += 1

        row += 1
        for res in rec.customer_product_price_ids:
            col = 0
            sheet.write(row, col, res.product_id.default_code, cell_format)
            col += 1
            sheet.write(row, col, res.product_id.name, cell_format)
            col += 1
            sheet.write(row, col, res.product_uom.name, cell_format)
            col += 1
            sheet.write(row, col, res.price, cell_format)
            col += 1
            row += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
