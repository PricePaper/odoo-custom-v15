# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

import json
import io
from odoo.tools import date_utils
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

class VendorProductLines(models.TransientModel):

    _name = 'vedor.product.lines'
    _description = 'Vendor Product Report Wizard Lines'


    parent_id = fields.Many2one('vedor.product.report.wizard', string="Parent Record")
    product_code = fields.Char(string='Product Code', related='product_id.default_code')
    product_name = fields.Char(string='Product Name', related='product_id.name')
    product_id = fields.Many2one('product.product', string='Product')
    product_uom = fields.Many2one('uom.uom', related='product_id.uom_id', string="UOM")
    ordered_qty = fields.Float(string='Ordered Qty')
    delivered_qty = fields.Float(string='Delivered Qty')


VendorProductLines()


class VendorProductReportWizard(models.TransientModel):

    _name = 'vedor.product.report.wizard'
    _description = "Vendor Product Report Wizard"

    vendor_ids = fields.Many2many('res.partner', string="Vendors")
    categ_ids = fields.Many2many('product.category', string="Category")
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')
    product_ids = fields.Many2many('product.product', string="Products")
    qty_selection = fields.Selection([('ordered', "Ordered Qty"), ('delivered', "Delivered Qty"),],
        string="Type", default='ordered')

    report_lines = fields.One2many('vedor.product.lines', 'parent_id', string="Sale Report")

    @api.multi
    def generate_products(self):
        if self.vendor_ids:
            res_prd = self.env['product.product']
            products = self.env['product.supplierinfo'].search([('name', 'in', self.vendor_ids.ids), '|', ('date_end', '=', False), ('date_end', '>', fields.Date.today())]).mapped('product_id')
            for product in products:
                vend_seq = product.seller_ids.filtered(lambda r: r.name in self.vendor_ids).mapped('sequence')
                non_seq = product.seller_ids.filtered(lambda r: r.name not in self.vendor_ids and (not r.date_end or r.date_end > fields.Date.today())).mapped('sequence')
                if not non_seq or min(vend_seq) <= min(non_seq):
                    res_prd |= product
            self.product_ids  = res_prd
        else:
            self.product_ids = False
            raise UserError(_('Vendor should be selected'))

    @api.multi
    def generate_lines(self):
        if not self.product_ids:
            raise UserError(_('There is no Product for the choosen criteria'))
        if not self.start_date or not self.end_date:
            raise UserError(_('Date Should be selected.'))
        if self.start_date > self.end_date:
            raise ValidationError('Start Date must be less than End Date')
        for rec in self:
            products = self.product_ids.ids + self.product_ids.mapped('superseded').mapped('old_product').ids
            if not products:
                self.report_lines = False
                return True
            query = """
                    SELECT l.product_id, sum(l.product_uom_qty), sum(l.qty_delivered), l.product_uom from sale_order o, sale_order_line
                    l WHERE o.confirmation_date >= '%s'
                    AND o.confirmation_date <= '%s' AND o.id=l.order_id AND
                    l.product_id in (%s) AND l.product_uom_qty>0 AND o.state IN ('sale', 'done') GROUP BY l.product_id, l.product_uom;""" % (
                str(rec.start_date), str(rec.end_date), (",".join(str(x) for x in products)))

            self.env.cr.execute(query)

            result = []
            # result is too large for fetchall()
            while True:
                rows = self.env.cr.fetchmany()

                if rows:
                    result.extend(rows)
                else:
                    break
            if not result:
                raise UserError(_('No sale data for the choosen date range'))
            out_lines = {}
            for result_line in result:
                product = self.env['product.product'].browse(result_line[0])
                if product.uom_id.id == result_line[3]:
                    if product in out_lines:
                        out_lines[product]['ordered_qty'] =  out_lines[product]['ordered_qty'] + result_line[1]
                        out_lines[product]['delivered_qty'] =  out_lines[product]['delivered_qty'] + result_line[2]
                    else:
                        out_lines[product] = {'ordered_qty': result_line[1], 'delivered_qty': result_line[2]}

                else:
                    uom = self.env['uom.uom'].browse(result_line[3])
                    ordered_qty = uom._compute_quantity(result_line[1], product.uom_id)
                    delivered_qty = uom._compute_quantity(result_line[2], product.uom_id)
                    if product in out_lines:
                        out_lines[product]['ordered_qty'] =  out_lines[product]['ordered_qty'] + ordered_qty
                        out_lines[product]['delivered_qty'] =  out_lines[product]['delivered_qty'] + delivered_qty
                    else:
                        out_lines[product] = {'ordered_qty': ordered_qty, 'delivered_qty': delivered_qty}
            report_lines=[]
            for prd, value in out_lines.items():
                report_lines.append((0, 0, {
                                'product_id': prd.id,
                                'ordered_qty': value['ordered_qty'],
                                'delivered_qty': value['delivered_qty'],
                                'parent_id': rec.id,
                                }))
            self.report_lines = False
            self.report_lines = report_lines
    @api.multi
    def print_pdf(self):
        return self.env.ref('purchase_extension.vendor_product_report').report_action(self)
    @api.multi
    def print_xlxs(self):

        data = {'rec' : self.id}
        return {
            'type': 'ir_actions_xlsx_download',
            'data': {'model': 'vedor.product.report.wizard',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Excel Report',
                     },
            'report_type': 'xlsx',
            }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format({'font_size': '12px'})
        head = workbook.add_format({'align': 'center', 'bold': True,'font_size':'20px'})
        txt = workbook.add_format({'font_size': '10px'})
        row, col = 0,0
        sheet.write(row, col, 'Product Code', cell_format)
        col+=1
        sheet.write(row, col, 'Product Name', cell_format)
        col+=1
        sheet.write(row, col, 'UOM', cell_format)
        col+=1
        sheet.write(row, col, 'Qty', cell_format)
        col+=1


        rec = self.env['vedor.product.report.wizard'].browse(data['rec'])
        row += 1

        for res in rec.report_lines:
            col = 0
            sheet.write(row, col, res.product_code, cell_format)
            col += 1
            sheet.write(row, col, res.product_name, cell_format)
            col += 1
            sheet.write(row, col, res.product_uom.name, cell_format)
            col += 1
            if rec.qty_selection == 'ordered':
                sheet.write(row, col, res.ordered_qty, cell_format)
            if rec.qty_selection == 'delivered':
                rec.write(row, col, res.delivered_qty, cell_format)
            col += 1
            row += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

VendorProductReportWizard()
