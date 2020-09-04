# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime,date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class SaleHistoryLinesWizard(models.TransientModel):

    _name = 'sale.history.lines.wizard'
    _description = 'Sales History Line Wizard'

    product_name = fields.Char(string='Product')
    product_uom = fields.Many2one('uom.uom', string="UOM")
    product_uom_qty = fields.Float(string='Quantity')
    date_order = fields.Char(string='Order Date')
    search_wizard_id = fields.Many2one('add.purchase.history.so', string='Parent')
    price_unit = fields.Float(string='Price')
    order_line = fields.Many2one('sale.order.line', string='Sale order line')
    qty_to_be = fields.Float(string='New Qty')
    product_category = fields.Many2one('product.category', string='Product Category')

SaleHistoryLinesWizard()


class AddPurchaseHistorySO(models.TransientModel):

    _name = 'add.purchase.history.so'
    _description = "Add Purchase History to SO Line"

    search_box = fields.Char(string='Search')
    purchase_history_ids = fields.One2many('sale.history.lines.wizard', 'search_wizard_id', string="Purchase History")
    sale_history_months = fields.Integer(string='Sales History For # Months ', default=lambda s: s.default_sale_history())

    @api.model
    def default_sale_history(self):
        if self.env.user.company_id and self.env.user.company_id.sale_history_months:
            return self.env.user.company_id.sale_history_months
        return 0


    @api.onchange('search_box', 'sale_history_months')
    def search_product(self):

        customer_id = self._context.get('customer_id', False)
        history_from = date.today() - relativedelta(months=self.sale_history_months)

        if customer_id:
            lines=[]
            line_ids = self.env['sale.history'].search([('partner_id', '=', customer_id), ('order_id.confirmation_date', '>=', history_from)])
            if self.search_box:
                for line in line_ids:
                    warning, price, price_from = line.order_line_id.calculate_customer_price()
                    if self.search_box.lower() in line.product_id.display_name.lower():
                        val = {
                                 'product_uom': line.uom_id.id,
                                 'date_order': line.order_id.confirmation_date,
                                 'order_line': line.order_line_id.id,
                                 'qty_to_be': 0.0,
                                 'price_unit': price,
                                 'product_uom_qty':line.order_line_id.product_uom_qty,
                                 'product_category': line.product_id.categ_id.id,
                                 'product_name': line.product_id.display_name
                                }
                        lines.append((0,0,val))
                self.purchase_history_ids = False
                self.purchase_history_ids = lines

            else:
                for line in line_ids:
                    warning, price, price_from = line.order_line_id.calculate_customer_price()
                    val = {
                             'product_uom': line.uom_id.id,
                             'date_order': line.order_id.confirmation_date,
                             'order_line': line.order_line_id.id,
                             'qty_to_be': 0.0,
                             'price_unit': price,
                             'product_uom_qty':line.order_line_id.product_uom_qty,
                             'product_category': line.product_id.categ_id.id,
                             'product_name': line.product_id.display_name
                            }
                    lines.append((0,0,val))
                self.purchase_history_ids = False
                self.purchase_history_ids = lines




    @api.multi
    def add_history_lines(self):
        """
        Creating saleorder line with purchase history lines
        """
        self.ensure_one()
        active_id = self._context.get('active_id')
        order_id = self.env['sale.order'].browse(active_id)
        line_ids = self.purchase_history_ids
        for line_id in line_ids:
            if line_id.qty_to_be != 0.0:
                warning, price, price_from = line_id.order_line.calculate_customer_price()
                sale_order_line = {'product_id' : line_id.order_line.product_id.id,
                                   'product_uom' : line_id.order_line.product_uom.id,
                                   'product_uom_qty' : line_id.qty_to_be,
                                   'price_unit' : price,
                                   'order_id' : order_id and order_id.id or False,
                                   'lst_price':line_id.order_line.product_id.lst_price,
                                   'price_from':line_id.order_line.price_from and line_id.order_line.price_from.id
                                   # 'working_cost':line_id.order_line.product_id.cost,
                }
                self.env['sale.order.line'].create(sale_order_line)
        return True


AddPurchaseHistorySO()
