# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import pytz


class SaleHistoryLinesWizard(models.TransientModel):
    _inherit = 'sale.history.lines.wizard'

    @api.onchange('qty_to_be', 'product_uom', )
    def _onchange_product_id_check_availability(self):
        if not self.qty_to_be or not self.product_uom:
            return {}

        product = self.order_line.product_id

        if product.type == 'product':
            order_id = self.env['sale.order'].browse(self._context.get('active_id'))
            message = ''
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            product = product.with_context(
                warehouse=order_id.warehouse_id.id,
                lang=order_id.partner_id.lang or self.env.user.lang or 'en_US'
            )
            product_qty = self.product_uom._compute_quantity(self.qty_to_be, product.uom_id)
            if float_compare(product.quantity_available - product.outgoing_quantity, product_qty, precision_digits=precision) == -1:
                is_mto = self.order_line.is_mto
                if not self.order_line.is_mto:
                    message += _(
                        'You plan to sell %s %s of %s but you only have %s %s available in %s warehouse.\n\n') % \
                               (self.qty_to_be, self.product_uom.name, self.product_name,
                                product.quantity_available - product.outgoing_quantity, product.uom_id.name, order_id.warehouse_id.name)
                    # We check if some products are available in other warehouses.
                    if float_compare(product.quantity_available - product.outgoing_quantity,
                        self.order_line.product_id.quantity_available - self.order_line.product_id.outgoing_quantity, precision_digits=precision) == -1:
                        message += _('There are %s %s available across all warehouses.\n\n') % \
                                   (self.order_line.product_id.quantity_available - self.order_line.product_id.outgoing_quantity, product.uom_id.name)
                        for warehouse in self.env['stock.warehouse'].search([]):
                            quantity = self.order_line.product_id.with_context(warehouse=warehouse.id).quantity_available - self.order_line.product_id.with_context(warehouse=warehouse.id).outgoing_quantity
                            if quantity > 0:
                                message += _(
                                    "%s: %s %s\n" % (warehouse.name, quantity, self.order_line.product_id.uom_id.name))

            if message:

                products = product.alternative_product_ids
                alternatives = ''
                if products:
                    alternatives = '\nPlease add an alternate product'
                    for item in products:
                        alternatives += '\n' + item.default_code
                    alternatives += '\nusing the Add Product button (not Browse Products).'
                if not product.allow_out_of_stock_order:
                    message1 = 'Product'+ product.display_name + 'is not in stock and can not be oversold.'
                    if alternatives:
                        message1 += alternatives
                    raise ValidationError(message1)
                return {'warning': {
                    'title': _('Not enough inventory!'),
                    'message': message+alternatives
                }}
        return {}


SaleHistoryLinesWizard()


class AddPurchaseHistorySO(models.TransientModel):
    _inherit = 'add.purchase.history.so'

    @api.onchange('sale_history_months', 'product_id', 'archived')
    def onchange_select_month(self):
        sale_history = self.sale_history_ids
        history_from = datetime.today() - relativedelta(months=self.sale_history_months)
        lines = []
        lines_temp = []

        if self.product_id and self.sale_history_months:
            sale_history = sale_history.filtered(
                lambda rec: rec.product_id.id == self.product_id.id and rec.order_id.date_order >= history_from)
        elif self.product_id:
            sale_history = sale_history.filtered(lambda rec: rec.product_id.id == self.product_id.id)
        elif self.sale_history_months:
            sale_history = sale_history.filtered(lambda rec: rec.order_id.date_order >= history_from)
        product_list = sale_history.mapped('product_id.id')
        for line in self.purchase_history_ids.filtered(lambda rec: rec.qty_to_be != 0.0):
            lines_temp.append((0, 0, {
                'product_uom': line.product_uom.id,
                'date_order': line.date_order,
                'order_line': line.order_line.id,
                'qty_to_be': line.qty_to_be,
                'qty_available': line.qty_available,
                'price_unit': line.price_unit,
                'old_price': line.old_price,
                'product_uom_qty': line.product_uom_qty,
                'product_category': line.product_category.id,
                'product_name': line.product_name
            }))

        self.purchase_history_temp_ids = lines_temp
        history_lines = self.purchase_history_temp_ids.mapped('order_line').ids
        sale_history = sale_history.filtered(lambda rec: rec.order_line_id.id not in history_lines)

        if sale_history:
            for line in sale_history.sorted(key=lambda l: l.product_id.categ_id.name):
                warning, price, price_from = line.order_line_id.calculate_customer_price()
                archived = False
                if not line.active or not line.product_id.active:
                    archived = True
                if archived and not self.archived or not archived and self.archived:
                    continue
                lines.append((0, 0, {
                    'product_uom': line.uom_id.id,
                    'date_order': line.order_id.date_order,
                    'order_line': line.order_line_id.id,
                    'qty_to_be': 0.0,
                    'qty_available': line.product_id.quantity_available - line.product_id.outgoing_quantity,
                    'price_unit': price,
                    'old_price': line.order_line_id.price_unit,
                    'product_uom_qty': line.order_line_id.product_uom_qty,
                    'product_category': line.product_id.categ_id.id,
                    'product_name': line.product_id.display_name,
                    'archived': archived,
                    'sale_ok': line.product_id.sale_ok
                }))

        self.purchase_history_ids = False

        return {
            'domain': {
                'product_id': [('id', 'in', product_list)]
            },
            'value': {
                'purchase_history_ids': lines,
            }
        }

    def add_history_lines(self):
        """
        Creating saleorder line with purchase history lines
        """
        self.ensure_one()
        active_id = self._context.get('active_id')
        order_id = self.env['sale.order'].browse(active_id)
        line_ids = self.purchase_history_ids | self.purchase_history_temp_ids
        for line_id in line_ids:
            if line_id.qty_to_be != 0.0:
                warning, price, price_from = line_id.order_line.calculate_customer_price()
                old_order_line = line_id.order_line
                last_sale = ''
                if old_order_line.order_id:
                    local = pytz.timezone(self.sudo().env.user.tz or "UTC")
                    last_date = datetime.strftime(
                        pytz.utc.localize(
                            datetime.strptime(
                                str(old_order_line.order_id.date_order), DEFAULT_SERVER_DATETIME_FORMAT)
                        ).astimezone(local), "%m/%d/%Y %H:%M:%S")
                    last_sale = 'Order Date  - %s\nPrice Unit    - %s\nSale Order  - %s' % (
                        last_date, old_order_line.price_unit, old_order_line.order_id.name)
                sale_order_line = {
                    'product_id': line_id.order_line.product_id.id,
                    'product_uom': line_id.order_line.product_uom.id,
                    'product_uom_qty': line_id.qty_to_be,
                    'price_unit': price,
                    'order_id': order_id and order_id.id or False,
                    'price_from': line_id.order_line.price_from and line_id.order_line.price_from.id,
                    'last_sale': last_sale
                }
                self.env['sale.order.line'].create(sale_order_line)
        return True


AddPurchaseHistorySO()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
