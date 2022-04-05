# -*- coding: utf-8 -*-

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models, fields, registry, api, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import ValidationError, AccessError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    release_date = fields.Datetime(string='Release Date')
    total_volume = fields.Float(string="Total Order Volume", compute='_compute_total_weight_volume')
    total_weight = fields.Float(string="Total Order Weight", compute='_compute_total_weight_volume')
    purchase_default_message = fields.Html(related="company_id.purchase_default_message", readonly=True)
    total_qty = fields.Float(string="Total Order Quantity", compute='_compute_total_weight_volume')
    vendor_delay = fields.Integer(related='partner_id.delay', string="Vendor Lead Time", readonly=True)
    vendor_order_freq = fields.Integer(related='partner_id.order_freq', string="Vendor Order Frequency", readonly=True)
    pickup_address_id = fields.Many2one('res.partner', string="Delivery Address")
    sale_order_count = fields.Integer(string="Sale Order Count", readonly=True, compute='_compute_sale_order_count')
    state = fields.Selection(selection_add=[
        ('in_progress', 'In Progress RFQ'),
        ('received', 'Received')])

    def action_rfq_send(self):
        """
         override to change model description for in progress
        """
        res = super().action_rfq_send()
        if self.state == 'in_progress':
            res['context']['model_description'] = 'Request for Quotation'
        return res

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_rfq_as_sent'):
            self.filtered(lambda rec: rec.state in ('draft', 'in_progress')).write({'state': 'sent'})
        return super(PurchaseOrder, self.with_context(mail_post_autofollow=self.env.context.get('mail_post_autofollow', True))).message_post(**kwargs)

    def action_in_progress(self):
        return self.write({'state': 'in_progress'})

    @api.depends('order_line.sale_order_id')
    def _compute_sale_order_count(self):
        for rec in self:
            rec.sale_order_count = len(rec._get_sale_orders()) or len(rec.order_line.mapped('sale_order_id').ids) or len(
                rec.order_line.mapped('move_dest_ids.sale_line_id.order_id').ids)

    @api.model
    def create(self, vals):
        if vals.get('partner_id'):
            purchase_rep = self.env['res.partner'].browse(vals.get('partner_id')).seller_partner_ids
            purchase_rep = purchase_rep and purchase_rep[0].user_ids
            if purchase_rep:
                vals['user_id'] = purchase_rep[0].id
            else:
                vals['user_id'] = self.env.user.id
        return super(PurchaseOrder, self).create(vals)

    @api.depends('order_line.product_id', 'order_line.product_qty')
    def _compute_total_weight_volume(self):
        for order in self:
            volume = 0
            weight = 0
            qty = 0
            for line in order.order_line:
                volume += line.gross_volume
                weight += line.gross_weight
                qty += line.product_qty
            order.total_volume = volume
            order.total_weight = weight
            order.total_qty = qty

    @api.model
    def sanitize_uom(self, result_dict):
        """
        processes the query result into a standard dictionary
        vals parameter for create argument of Odoo
        """
        # Converts the result_dict quantities to purchase unit scale
        for ele in result_dict.keys():
            product_purchase_unit = self.env['product.product'].browse(ele).uom_po_id
            for row in result_dict[ele]:
                if row['uom'] != product_purchase_unit.id:
                    changed_uom_qty = self.env['uom.uom'].browse(row['uom'])._compute_quantity(row['units'],
                                                                                               product_purchase_unit)
                    row['uom'] = product_purchase_unit.id
                    row['units'] = changed_uom_qty

        # merges values of same period to a single record
        result_dict2 = {}
        for ele in result_dict.keys():
            result_dict2.update({ele: {}})
            for row in result_dict[ele]:
                if not result_dict2[ele].get(row['period'], False):
                    result_dict2[ele].update({row['period']: row['units']})
                else:
                    current_count = result_dict2[ele].get(row['period'])
                    result_dict2[ele].update({row['period']: row['units'] + current_count})

        # Formats the result to a key value pair where key is the product id and values is a dictionary with key as period and value as quantity
        current_date = date.today()
        first_day = current_date.replace(day=1)
        first_month_list = [str((first_day + relativedelta(months=-x)).strftime('%Y-%m-%d %H:%M:%S')) for x in
                            range(0, 15)]
        date_matrix = {datetime.strptime(ele, "%Y-%m-%d %H:%M:%S"): 'month' + str(x) for x, ele in
                       zip(range(1, 16), first_month_list)}
        for key in result_dict2.keys():
            result = {}
            for ele in date_matrix.keys():
                if ele in result_dict2[key].keys():
                    result.update({date_matrix[ele]: result_dict2[key][ele]})
                else:
                    result.update({date_matrix[ele]: 0})
            result_dict2[key] = result

        # Converts the result into list of standard dictionarys vals parameter for create argument in Odoo
        result_list = []
        for k in result_dict2.keys():
            month_data = result_dict2[k]
            month_data.update({'product_id': k,
                               'product_pseudo_id': k,
                               })
            result_list.append(month_data)
        return result_list

    def add_sale_history_to_po_line(self):
        if not self.partner_id:
            return False
        result_list = []
        all_supplier_info = self.env['product.supplierinfo'].search([('name', '=', self.partner_id.id)])
        all_vendor_products = []
        existing_products = []
        if self.order_line:
            prdts = self.order_line.mapped('product_id')
            existing_products = prdts and prdts.ids or []
        for rec in all_supplier_info:
            if rec.product_id:
                if rec.product_id.id in existing_products:
                    continue
                if rec.product_id.purchase_ok:
                    all_vendor_products.append(rec.product_id.id)
            else:
                prod_ids = rec.product_tmpl_id.product_variant_ids and \
                           rec.product_tmpl_id.product_variant_ids.filtered(lambda p: p.purchase_ok).ids or []
                for prod in prod_ids:
                    if prod in existing_products:
                        continue
                    all_vendor_products.append(prod)

        product_ids = tuple(all_vendor_products) if len(all_vendor_products) > 1 else all_vendor_products and \
                                                                                      all_vendor_products[0] or 0
        operator = 'in' if len(all_vendor_products) > 1 else '='
        if all_vendor_products:
            current_date = date.today()
            first_day = current_date.replace(day=1)
            date_limit = str(first_day + relativedelta(months=-15))
            self._cr.execute(
                "SELECT date_trunc('month', so.date_order) AS cnf_date, "
                "sol.product_id, sol.product_uom, sum(sol.product_uom_qty) "
                "FROM sale_order_line sol JOIN sale_order so on so.id=sol.order_id "
                "WHERE so.state in ('sale', 'done') AND sol.product_id %s %s and so.date_order >= '%s' "
                "GROUP BY sol.product_id, sol.product_uom, cnf_date "
                "ORDER BY sol.product_id, sol.product_uom, cnf_date desc" % (operator, product_ids, str(date_limit)))

            res = self._cr.dictfetchall()
            if not res:
                raise ValidationError(_('No history of products found being sold in the last 15 months.'))
            result_dict = {}
            product_id = False
            for element in res:
                if product_id != element['product_id']:
                    product_id = element['product_id']
                    result_dict.update({product_id: [{
                        'period': element['cnf_date'],
                        'units': element['sum'],
                        'uom': element['product_uom'],
                    }]})
                else:
                    result_dict[product_id].append({'period': element['cnf_date'],
                                                    'units': element['sum'],
                                                    'uom': element['product_uom'],
                                                    })
            result_list = self.sanitize_uom(result_dict)
        context = {'data': result_list, 'default_vendor_id': self.partner_id.id}
        view_id = self.sudo().env.ref('purchase_extension.view_sale_history_add_po_wiz').id
        return {
            'name': _('Add sale history to PO'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'add.sale.history.po',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new'
        }

    def button_confirm(self):
        """
        cancel all other RFQ under the same purchase agreement
        """
        for purchase_order in self:
            orders = self.search(
                [('requisition_id', '!=', False), ('requisition_id', '=', purchase_order.requisition_id.id),
                 ('id', 'not in', purchase_order.ids)])
            orders.button_cancel()
            tr = ''

            for line in purchase_order.order_line:
                product = line.product_id
                if round(line.product_id.standard_price, 2) != line.price_unit:
                    tr += '''<tr>
                        <td><b>{}</b></td>
                        <td><b>${cost:.2f}</b></td>
                        <td style="color:red"><b>${price:.2f}</b></td>
                    </tr>'''.format(product.display_name, cost=product.standard_price, price=line.price_unit)
            if tr:
                note = '''
                <table class="table table-bordered">
                    <tbody>
                    <tr><td><b>Product</b></td><td><b>Cost</b></td><td><b>PO Price</b></td></tr>
                    {}
                    </tbody>
                </table>
                '''.format(tr)
                activity_vals = {
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'user_id': purchase_order.user_id.id if purchase_order.user_id else self.env.user.id
                }
                purchase_order.activity_schedule(summary="Cost Discrepancy", note=note, **activity_vals)
        return super(PurchaseOrder, self).button_confirm()

    @api.depends('state', 'order_line.qty_to_invoice')
    def _get_invoiced(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for order in self:
            if order.state not in ('purchase', 'received', 'done'):
                order.invoice_status = 'no'
                continue

            if any(
                    not float_is_zero(line.qty_to_invoice, precision_digits=precision)
                    for line in order.order_line.filtered(lambda l: not l.display_type)
            ):
                order.invoice_status = 'to invoice'
            elif (
                    all(
                        float_is_zero(line.qty_to_invoice, precision_digits=precision)
                        for line in order.order_line.filtered(lambda l: not l.display_type)
                    )
                    and order.invoice_ids
            ):
                order.invoice_status = 'invoiced'
            else:
                order.invoice_status = 'no'

    def _add_supplier_to_product(self):
        # Add the partner in the supplier list of the product if the supplier is not registered for
        # this product.
        for line in self.order_line:
            # Do not add a contact as a supplier
            partner = self.partner_id if not self.partner_id.parent_id else self.partner_id.parent_id

            vendor_prices = line.product_id.seller_ids.filtered(
                lambda r: r.name == self.partner_id and r.min_qty <= line.product_qty)

            # Convert the price in the right currency.
            currency = partner.property_purchase_currency_id or self.env.user.company_id.currency_id
            price = self.currency_id._convert(line.price_unit, currency, line.company_id, line.date_order or fields.Date.today(), round=False)
            # Compute the price for the template's UoM, because the supplier's UoM is related to that UoM.
            if line.product_id.product_tmpl_id.uom_po_id != line.product_uom:
                default_uom = line.product_id.product_tmpl_id.uom_po_id
                price = line.product_uom._compute_price(price, default_uom)

            supplierinfo = self._prepare_supplier_info(partner, line, price, currency)
            seller = line.product_id._select_seller(
                partner_id=line.partner_id,
                quantity=line.product_qty,
                date=line.order_id.date_order and line.order_id.date_order.date(),
                uom_id=line.product_uom)
            if seller:
                supplierinfo['product_name'] = seller.product_name
                supplierinfo['product_code'] = seller.product_code
            vals = {
                'seller_ids': [(0, 0, supplierinfo)],
            }
            try:
                if not vendor_prices:
                    line.product_id.with_context({'user': self.user_id and self.user_id.id, 'from_purchase': True}).write(vals)
                else:
                    vendor_line = vendor_prices.sorted(key=lambda r: r.min_qty, reverse=True)[0]
                    if vendor_line.price != price:
                        vendor_line.with_context({'user': self.env.user.id and self.env.user.id, 'from_purchase': True}).price = price

            except AccessError:  # no write access rights -> just ignore
                break

    def button_received(self):
        return self.write({'state': 'received'})


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    gross_volume = fields.Float(string="Gross Volume", compute='_compute_gross_weight_volume')
    gross_weight = fields.Float(string="Gross Weight", compute='_compute_gross_weight_volume')


    def _get_stock_move_price_unit(self):

        self.ensure_one()
        order = self.order_id
        price_unit = self.price_unit
        price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')
        if self.taxes_id:
            qty = self.product_qty or 1
            price_unit = self.taxes_id.with_context(round=False).compute_all(
                price_unit, currency=self.order_id.currency_id, quantity=qty, product=self.product_id, partner=self.order_id.partner_id
            )['total_void']
            price_unit = float_round(price_unit / qty, precision_digits=price_unit_prec)
        # if self.product_uom.id != self.product_id.uom_id.id:
        #     price_unit *= self.product_uom.factor / self.product_id.uom_id.factor
        if order.currency_id != order.company_id.currency_id:
            price_unit = order.currency_id._convert(
                price_unit, order.company_id.currency_id, self.company_id, self.date_order or fields.Date.today(), round=False)
        return price_unit

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        res = super(PurchaseOrderLine, self)._onchange_quantity()
        date_order = self.order_id.date_order
        delay = self.order_id.vendor_delay
        if date_order and delay:
            planned_date = date_order + relativedelta(days=delay)
            self.date_planned = planned_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return res

    @api.model
    def create(self, vals):
        res = super(PurchaseOrderLine, self).create(vals)
        if res.order_id and res.order_id.state == 'purchase':
            self._add_supplier_to_product()
        res.filtered(lambda l: l.order_id.state == 'received')._create_or_update_picking()
        return res

    def _add_supplier_to_product(self):
        # Add the partner in the supplier list of the product if the supplier is not registered for
        # this product.
        for line in self:
            # Do not add a contact as a supplier
            partner = self.order_id.partner_id if not self.order_id.partner_id.parent_id else self.order_id.partner_id.parent_id

            vendor_prices = line.product_id.seller_ids.filtered(
                lambda r: r.name == self.order_id.partner_id and r.min_qty <= line.product_qty)

            # Convert the price in the right currency.
            currency = partner.property_purchase_currency_id or self.env.user.company_id.currency_id
            price = self.order_id.currency_id._convert(line.price_unit, currency, line.company_id, line.date_order or fields.Date.today(), round=False)
            # Compute the price for the template's UoM, because the supplier's UoM is related to that UoM.
            if line.product_id.product_tmpl_id.uom_po_id != line.product_uom:
                default_uom = line.product_id.product_tmpl_id.uom_po_id
                price = line.product_uom._compute_price(price, default_uom)

            supplierinfo = self.order_id._prepare_supplier_info(partner, line, price, currency)
            seller = line.product_id._select_seller(
                partner_id=line.partner_id,
                quantity=line.product_qty,
                date=line.order_id.date_order and line.order_id.date_order.date(),
                uom_id=line.product_uom)
            if seller:
                supplierinfo['product_name'] = seller.product_name
                supplierinfo['product_code'] = seller.product_code
            vals = {
                'seller_ids': [(0, 0, supplierinfo)],
            }
            try:
                if not vendor_prices:
                    line.product_id.with_context({'user': self.env.user.id and self.env.user.id, 'from_purchase': True}).write(vals)
                else:
                    vendor_line = vendor_prices.sorted(key=lambda r: r.min_qty, reverse=True)[0]
                    if vendor_line.price != price:
                        vendor_line.with_context({'user': self.env.user.id and self.env.user.id, 'from_purchase': True}).price = price

            except AccessError:  # no write access rights -> just ignore
                break

    def write(self, vals):
        lines = self.filtered(lambda l: l.order_id.state == 'received')
        previous_product_qty = {line.id: line.product_uom_qty for line in lines}
        res = super(PurchaseOrderLine, self.with_context({'from_purchase_write': True})).write(vals)
        if 'product_qty' in vals:
            lines.with_context(previous_product_qty=previous_product_qty)._create_or_update_picking()
        for rec in self:
            if rec.order_id and rec.order_id.picking_ids:
                for picking in rec.order_id.picking_ids.filtered(lambda r: r.state != 'done'):
                    for move in picking.move_lines:
                        move.price_unit = move._get_price_unit()
        if vals.get('price_unit'):
            if self.order_id and self.order_id.state == 'purchase':
                self._add_supplier_to_product()
        return res

    @api.model
    def schedule_update_date_po_line(self):
        order_lines = self.env['purchase.order'].search([('state', 'in', ('draft', 'sent'))]).mapped('order_line')
        for line in order_lines:
            params = {'order_id': line.order_id}
            seller = line.product_id._select_seller(
                partner_id=line.partner_id,
                quantity=line.product_qty,
                date=line.order_id.date_order and line.order_id.date_order.date(),
                uom_id=line.product_uom,
                params=params)
            date_order = datetime.today()
            if line.order_id.date_order and date_order < line.order_id.date_order:
                date_order = line.order_id.date_order
            if seller:
                line.date_planned = date_order + relativedelta(days=seller.delay if seller else 0)
            else:
                line.date_planned = date_order + relativedelta(days=line.partner_id.delay if line.partner_id else 0)

    def show_sales_history(self):
        """
        returns the historical sales of this
        product for the past 15 months
        """
        current_date = date.today()
        first_day = current_date.replace(day=1)
        date_limit = str(first_day + relativedelta(months=-15))
        self._cr.execute(
            "SELECT sol.id FROM sale_order_line sol JOIN sale_order so on so.id=sol.order_id WHERE sol.product_id=%s AND so.date_order>='%s' and so.state in ('sale', 'done')" % (
                self.product_id.id, date_limit))
        res = self._cr.dictfetchall()
        sale_lines = [ele['id'] for ele in res]
        sale_lines = self.env['sale.order.line'].browse(sale_lines)
        if not sale_lines:
            raise ValidationError(_('No history of product found being sold in the last 15 months.'))
        created_ids = []
        for ele in sale_lines:
            uom_qty = ele.product_uom_qty
            # change uom to purchase units
            if ele.product_uom.id != ele.product_id.uom_po_id.id:
                uom_qty = ele.product_uom._compute_quantity(uom_qty, ele.product_id.uom_po_id)
            created_ids += self.env['view.sales.history.po'].create({
                'product_id': ele.product_id.id,
                'date': ele.order_id.date_order,
                'quantity': uom_qty,
                'uom': ele.product_id.uom_po_id.id,
                'partner_id': ele.order_id.partner_id.id,
                'sale_line_id': ele.id,
            })
        action = self.sudo().env.ref('purchase_extension.action_view_sales_history_po').read()[0]
        action['domain'] = [("id", "in", [r.id for r in created_ids])]
        action['target'] = 'new'
        return action

    @api.depends('product_id.volume', 'product_id.weight')
    def _compute_gross_weight_volume(self):
        for line in self:
            volume = line.product_id.volume * line.product_qty
            weight = line.product_id.weight * line.product_qty
            line.gross_volume = volume
            line.gross_weight = weight

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
