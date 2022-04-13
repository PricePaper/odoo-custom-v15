# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class PosSaleReport(models.Model):
    _name = "sales.analysis.report"
    _description = "Sales Analysis (All in One)"
    _order = "product_qty asc"
    _auto = False

    name = fields.Char('Order Reference', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', readonly=True)
    date_invoice = fields.Datetime(string='Date Invoice', readonly=True)
    user_id = fields.Many2one('res.users', 'Salesperson', readonly=True)
    categ_id = fields.Many2one('product.category', 'Product Category', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    country_id = fields.Many2one('res.country', 'Partner Country', readonly=True)
    sales_dollars = fields.Float(string='Sales dollars', readonly=True)
    profit_dollars = fields.Float(string='Profit dollars', readonly=True)
    product_qty = fields.Float('Product Quantity', readonly=True)

    #TODO test the querry result with migrated db data v15
    def _inv(self):
        so_str = """
                SELECT  inv_line.id AS id,
                inv.name AS name,
                inv.partner_id AS partner_id,
                inv_line.product_id AS product_id,
                pro.product_tmpl_id AS product_tmpl_id,
                inv.invoice_date AS date_invoice,
                (inv_line.quantity / u.factor * u2.factor) as product_qty,
                inv_line.price_unit,
                COALESCE(so_line.working_cost, 0.00) AS product_cost,
                (CASE 
                    WHEN so_line.is_delivery = true 
                        THEN ROUND(CAST(COALESCE((inv_line.price_subtotal - dc.average_company_cost) * inv_line.quantity, 0.00) AS NUMERIC), 2)
                    ELSE COALESCE((inv_line.price_unit - so_line.working_cost) * inv_line.quantity, 0.00)
                END) AS profit_dollars,
                inv.invoice_user_id AS user_id,
                pt.categ_id AS categ_id,
                inv.company_id AS company_id,
                inv_line.price_total AS sales_dollars,
                rp.country_id AS country_id,
                inv_line.price_subtotal AS price_subtotal 
        FROM account_move_line inv_line
            JOIN sale_order_line_invoice_rel sl ON (inv_line.id = sl.invoice_line_id)
            JOIN sale_order_line so_line ON (so_line.id = sl.order_line_id)
            JOIN sale_order so ON (so_line.order_id = so.id)
            JOIN delivery_carrier dc ON (so.carrier_id = dc.id)
            JOIN account_move inv ON (inv_line.move_id = inv.id)
            LEFT JOIN product_product pro ON (inv_line.product_id = pro.id)
            JOIN res_partner rp ON (inv.partner_id = rp.id)
            LEFT JOIN product_template pt ON (pro.product_tmpl_id = pt.id)
            LEFT JOIN uom_uom u on (u.id=inv_line.product_uom_id)
            LEFT JOIN uom_uom u2 on (u2.id=pt.uom_id)
        WHERE inv.state in ('posted') and inv.payment_state in ('in_payment','paid','partial')
        """
        return so_str

    def _from(self):
        return """(%s)""" % (self._inv())

    def get_main_request(self):
        request = """
            CREATE or REPLACE VIEW %s AS
                SELECT id AS id,
                    name,
                    partner_id,
                    product_id,
                    product_tmpl_id,
                    product_qty,
                    date_invoice,
                    user_id,
                    categ_id,
                    company_id,
                    sales_dollars,
                    profit_dollars,
                    country_id
                FROM %s
                AS foo""" % (self._table, self._from())
        return request

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self.get_main_request())
