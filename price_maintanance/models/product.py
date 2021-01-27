# -*- coding: utf-8 -*-

import logging
import statistics
from datetime import datetime, date

from dateutil.relativedelta import relativedelta

from odoo import fields, models, api, _
from odoo.addons.price_paper.models import margin
from odoo.addons.queue_job.job import job
from odoo.tools import float_round

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    last_purchase_price = fields.Char(string='Last Purchase Price', compute='compute_last_purchase_price', store=False)
    last_po = fields.Many2one('purchase.order', string='Last PO', compute='compute_last_purchase_price', store=False)
    competitor_price_ids = fields.One2many('customer.product.price', 'product_id', string='Competitor prices',
                                           domain=[('pricelist_id.type', '=', 'competitor')])
    customer_price_ids = fields.One2many('customer.product.price', 'product_id',
                                         domain=[('pricelist_id.type', '=', 'customer')], string='Customer prices')
    median_price = fields.Html(string='Median Prices')
    future_price_ids = fields.One2many('cost.change', 'product_id', string='Future Price',
                                       domain=[('is_done', '=', False), ('product_id', '!=', False)])
    change_flag = fields.Boolean(string='Log an Audit Note')
    audit_notes = fields.Text(string='Audit Note')

    @api.multi
    def edit_price(self):
        context = {'product_id': self.id, 'lst_price': self.lst_price, 'cost': self.standard_price,
                   'customer_pricelist': self.customer_price_ids.ids, 'future_price': self.future_price_ids.ids}
        view_id = self.env.ref('price_maintanance.view_price_maintanace_edit').id
        return {
            'name': _('Edit Price'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'price.maintanace.edit',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }

    @api.multi
    def compute_last_purchase_price(self):

        for product in self:
            line = self.env['purchase.order.line'].search(
                [('state', 'in', ('done', 'purchase')), ('product_id', '=', product.id)], order='date_order desc',
                limit=1)
            if line:
                product.last_purchase_price = '%s %s %s' % (line.price_unit, line.product_uom.name, line.date_order)
                product.last_po = line.order_id.id

    def get_median(self, order_lines):

        prices = {}
        median = {}
        for line in order_lines:
            product_price = line.price_unit + line.product_id.price_extra
            if line.product_uom.id in prices:
                prices[line.product_uom.id].append(product_price)
            else:
                prices[line.product_uom.id] = [product_price]
        for uom in prices:
            try:
                median[uom] = round(statistics.median_high(prices[uom]), 2)
            except statistics.StatisticsError as e:
                median[uom] = 0
        return median

    @api.model
    def _calculate_median_price(self):
        today = datetime.now()
        date_10_days_back_start_date = today - relativedelta(days=10)
        date_30_days_back_start_date = today - relativedelta(days=30)
        date_60_days_back_start_date = today - relativedelta(days=60)
        date_90_days_back_start_date = today - relativedelta(days=90)

        unit_price_median_10_day = 100
        orders = self.env['sale.order'].search(
            [('state', 'in', ['sale', 'done']), ('confirmation_date', '>=', str(date_90_days_back_start_date)),
             ('confirmation_date', '<=', str(today))])
        order_lines = self.env['sale.order.line']

        for order in orders:
            order_lines |= order.order_line

        products = self.env['product.product'].search([])
        for product in products:
            sale_order_lines_10_day_back = order_lines.filtered(lambda
                                                                    line: line.product_id.id == product.id and line.order_id.confirmation_date >= date_10_days_back_start_date)
            sale_order_lines_30_day_back = order_lines.filtered(lambda
                                                                    line: line.product_id.id == product.id and line.order_id.confirmation_date >= date_30_days_back_start_date)
            sale_order_lines_60_day_back = order_lines.filtered(lambda
                                                                    line: line.product_id.id == product.id and line.order_id.confirmation_date >= date_60_days_back_start_date)
            sale_order_lines_90_day_back = order_lines.filtered(lambda
                                                                    line: line.product_id.id == product.id and line.order_id.confirmation_date >= date_90_days_back_start_date)
            unit_price_median_10_day = product.get_median(sale_order_lines_10_day_back)
            unit_price_median_30_day = product.get_median(sale_order_lines_30_day_back)
            unit_price_median_60_day = product.get_median(sale_order_lines_60_day_back)
            unit_price_median_90_day = product.get_median(sale_order_lines_90_day_back)
            sale_uoms = product.sale_uoms.ids
            median_price = ""
            for uom in sale_uoms:
                name = self.env['uom.uom'].browse(uom).name
                median_price += "<table style='width:500px'>\
                                <tr><th>{}</th></tr>\
                                <tr><th>Number of Days</th><th>Median</th></tr>\
                                <tr><td>10 Days</td><td>$ {:.02f}</td></tr>\
                                <tr><td>30 Days</td><td>$ {:.02f}</td></tr>\
                                <tr><td>60 Days</td><td>$ {:.02f}</td></tr>\
                                <tr><td>90 Days</td><td>$ {:.02f}</td></tr>\
                                </table>".format(name, unit_price_median_10_day.get(uom, 0),
                                                 unit_price_median_30_day.get(uom, 0),
                                                 unit_price_median_60_day.get(uom, 0),
                                                 unit_price_median_90_day.get(uom, 0))
            product.median_price = median_price

    @api.multi
    def write(self, vals):
        change_flag = vals.pop('change_flag', False)
        audit_notes = vals.pop('audit_notes', False)
        res = super(ProductProduct, self).write(vals)
        if change_flag:
            self.create_audit_notes(audit_notes)
        if vals.get('future_price_ids', False):
            self.cost_change_cron_button()
        return res

    @api.multi
    def cost_change_cron_button(self):
        self.env['cost.change'].cost_change_cron()
        return True

    @api.multi
    def create_audit_notes(self, audit_notes):
        for product in self:
            product.env['price.edit.notes'].create({
                'product_id': product.id,
                'edit_date': fields.Datetime.now(),
                'note': audit_notes,
                'user_id': self.env.user.id
            })

    @api.model
    def _cron_update_product_lst_price(self):

        products = self.env['product.product'].search([])
        similar_products = []
        for product in products:
            if product.id in similar_products:
                continue
            if product.standard_price_date_lock and product.standard_price_date_lock > date.today():
                continue

            if product.similar_product_ids:
                similar_products += product.similar_product_ids.ids
            product.standard_price_date_lock = False
            product.with_delay(channel='root.standardprice').job_queue_standard_price_update()

    @job
    @api.multi
    def job_queue_standard_price_update(self):

        date_to = datetime.today() - relativedelta(months=self.env.user.company_id.product_lst_price_months or 0, day=1)
        product_list = self
        if self.similar_product_ids:
            product_list += self.similar_product_ids
        sale_uoms = product_list.mapped('sale_uoms')
        for uom in sale_uoms:

            domain = [
                ('display_type', '=', False),
                ('order_id.date_order', '>=', date_to.strftime('%Y-%m-%d')),
                ('order_id.state', 'in', ['sale', 'done']),
                ('product_uom', '=', uom.id),
                ('product_id', 'in', product_list.ids)
            ]
            OrderLine = self.env['sale.order.line']
            lines = OrderLine.search(domain, order="confirmation_date desc")
            partners = lines.mapped('order_id.partner_id')
            partner_count = len(partners)
            partner_count_company = self.env.user.company_id.partner_count or 0
            new_lst_price = 0
            if partner_count >= partner_count_company:
                try:
                    new_lst_price = statistics.median_high(
                        [lines.filtered(lambda l: l.order_id.partner_id == partner)[:1].price_unit for partner in
                         partners])

                except statistics.StatisticsError as e:
                    _logger.error('Not enough data to find mean price for product_id: {}.'.format(self.id))
                    new_lst_price = self.get_price_from_competitor_or_categ
            else:
                new_lst_price = self.get_price_from_competitor_or_categ(uom)
            new_lst_price = float_round(new_lst_price, precision_digits=2)
            for product in product_list:
                if uom in product.sale_uoms:
                    uom_rec = product.uom_standard_prices.filtered(lambda p: p.uom_id == uom)
                    if uom_rec:
                        if uom_rec.price != new_lst_price:
                            uom_rec.with_context({'from_standardprice_cron': True}).price = new_lst_price
                    else:
                        vals = {'product_id': product.id,
                                'uom_id': uom.id,
                                'price': new_lst_price}
                        self.env['product.standard.price'].with_context({'from_standardprice_cron': True}).create(vals)
        return True

    def get_price_from_competitor_or_categ(self, uom):
        new_lst_price = 0
        cost = self.cost
        restaurant_id = self.env.ref('website_scraping.website_scraping_cofig_1').id
        webstaurant_id = self.env.ref('website_scraping.website_scraping_cofig_2').id
        new_lst_price = self.get_from_competitor(restaurant_id, uom)
        if not new_lst_price:
            new_lst_price = self.get_from_competitor(webstaurant_id, uom)
        if not new_lst_price:
            if uom != self.uom_id:
                uom_cost = float_round(self.uom_id._compute_price(cost, uom), precision_digits=2)
                cost = float_round(uom_cost * (1 + (self.categ_id.repacking_upcharge / 100)), precision_digits=2)
            new_lst_price = margin.get_price(cost, self.categ_id.standard_price, percent=True)
        return new_lst_price

    def get_from_competitor(self, competitor_id, uom):
        new_lst_price = 0
        pricelist = self.env['product.pricelist'].search([
            ('type', '=', 'competitor'),
            ('competitor_id', '=', competitor_id),
            ('competietor_margin', '=', 10)])
        pricelist_line = pricelist.customer_product_price_ids.filtered(lambda p: p.product_id == self)
        if pricelist_line:
            new_lst_price = float_round(pricelist_line[0].product_uom._compute_price(pricelist_line[0].price, uom),
                                        precision_digits=2)
            if uom != self.uom_id:
                competitor_price = float_round(new_lst_price * (1 + (self.categ_id.repacking_upcharge / 100)),
                                               precision_digits=2)
                new_lst_price = margin.get_price(competitor_price, self.categ_id.standard_price, percent=True)
        return new_lst_price


ProductProduct()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
