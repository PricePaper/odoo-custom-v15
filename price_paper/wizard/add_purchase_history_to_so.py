# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import pytz


class SaleHistoryLinesWizard(models.TransientModel):
    _name = 'sale.history.lines.wizard'
    _description = 'Sales History Line Wizard'

    product_name = fields.Char(string='Product')
    product_uom = fields.Many2one('uom.uom', string="UOM")
    product_uom_qty = fields.Float(string='Quantity')
    date_order = fields.Char(string='Order Date')
    search_wizard_id = fields.Many2one('add.purchase.history.so', string='Parent')
    price_unit = fields.Float(string='Price')
    old_price = fields.Float(string='History Price')
    order_line = fields.Many2one('sale.order.line', string='Sale order line')
    qty_to_be = fields.Float(string='New Qty')
    product_category = fields.Many2one('product.category', string='Product Category')
    search_wizard_temp_id = fields.Many2one('add.purchase.history.so', string='Parent Win')
    qty_available = fields.Float(string='Available Qty')
    archived = fields.Boolean(string='Archived')
    sale_ok = fields.Boolean(string='Can be sold')

    def _check_routing(self, order_id, product):
        is_available = False

        product_routes = product.route_ids + product.categ_id.total_route_ids

        # Check MTO
        wh_mto_route = order_id.warehouse_id.mto_pull_id.route_id
        if wh_mto_route and wh_mto_route <= product_routes:
            is_available = True
        else:
            mto_route = False
            try:
                mto_route = self.env['stock.warehouse']._find_global_route('stock.route_warehouse0_mto',  _('Make To Order'))
            except UserError:
                # if route MTO not found in ir_model_data, we treat the product as in MTS
                pass
            if mto_route and mto_route in product_routes:
                is_available = True

        # Check Drop-Shipping
        if not is_available:
            for pull_rule in product_routes.mapped('rule_ids'):
                if pull_rule.picking_type_id.sudo().default_location_src_id.usage == 'supplier' and \
                        pull_rule.picking_type_id.sudo().default_location_dest_id.usage == 'customer':
                    is_available = True
                    break

        return is_available

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
            if float_compare(product.qty_available - product.outgoing_qty, product_qty, precision_digits=precision) == -1:
                is_mto = self.order_line.is_mto
                if not self.order_line.is_mto:
                    message += _(
                        'You plan to sell %s %s of %s but you only have %s %s available in %s warehouse.\n\n') % \
                               (self.qty_to_be, self.product_uom.name, self.product_name,
                                product.qty_available - product.outgoing_qty, product.uom_id.name, order_id.warehouse_id.name)
                    # We check if some products are available in other warehouses.
                    if float_compare(product.qty_available - product.outgoing_qty,
                        self.order_line.product_id.qty_available - self.order_line.product_id.outgoing_qty, precision_digits=precision) == -1:
                        message += _('There are %s %s available across all warehouses.\n\n') % \
                                   (self.order_line.product_id.qty_available - self.order_line.product_id.outgoing_qty, product.uom_id.name)
                        for warehouse in self.env['stock.warehouse'].search([]):
                            quantity = self.order_line.product_id.with_context(warehouse=warehouse.id).qty_available - self.order_line.product_id.with_context(warehouse=warehouse.id).outgoing_qty
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
    _name = 'add.purchase.history.so'
    _description = "Add Purchase History to SO Line"

    search_box = fields.Char(string='Search')
    purchase_history_ids = fields.One2many('sale.history.lines.wizard', 'search_wizard_id', string="Purchase History")
    sale_history_months = fields.Integer(string='Sales History For # Months ',
                                         default=lambda s: s.default_sale_history())
    product_id = fields.Many2one('product.product', string='Product')
    purchase_history_temp_ids = fields.One2many('sale.history.lines.wizard', 'search_wizard_temp_id',
                                                string="Purchase History Temp")
    show_cart = fields.Boolean(string="Show Cart")
    sale_history_ids = fields.Many2many('sale.history')
    archived = fields.Boolean(string='Archived')

    @api.model
    def default_sale_history(self):
        if self.env.user.company_id and self.env.user.company_id.sale_history_months:
            return self.env.user.company_id.sale_history_months
        return 0

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
                    'qty_available': line.product_id.qty_available - line.product_id.outgoing_qty,
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
                # self.env['sale.order.line'].create(sale_order_line)
                order_id.write({
                    'order_line': [0, 0, sale_order_line]
                })
        return True



AddPurchaseHistorySO()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
