# -*- coding: utf-8 -*-
import json
import operator as py_operator
from lxml import etree
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round
from datetime import timedelta, time
from odoo.osv import expression

OPERATORS = {
    '<': py_operator.lt,
    '>': py_operator.gt,
    '<=': py_operator.le,
    '>=': py_operator.ge,
    '=': py_operator.eq,
    '!=': py_operator.ne
}


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # def action_open_quants(self):
    #     return {}

    description_purchase = fields.Text(
        'Purchase Description', translate=True, copy=False)

    def _get_product_accounts(self):
        """ Add the stock accounts related to product to the result of super()
        @return: dictionary which contains information regarding stock accounts and super (income+expense accounts)
        """
        accounts = super(ProductTemplate, self)._get_product_accounts()
        accounts.update({
            'sc_liability_out': self.categ_id.sc_stock_liability_account_id
        })
        return accounts

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            product_ids = []
            if operator in positive_operators:
                product_ids = list(self._search([('default_code', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid))
                if not product_ids:
                    product_ids = list(self._search([('barcode', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid))
            if not product_ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                product_ids = list(self._search(args + [('default_code', operator, name)], limit=limit))
                if not limit or len(product_ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    limit2 = (limit - len(product_ids)) if limit else False
                    product2_ids = self._search(args + [('name', operator, name), ('id', 'not in', product_ids)], limit=limit2, access_rights_uid=name_get_uid)
                    product_ids.extend(product2_ids)
            elif not product_ids and operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = expression.OR([
                    ['&', ('default_code', operator, name), ('name', operator, name)],
                    ['&', ('default_code', '=', False), ('name', operator, name)],
                ])
                domain = expression.AND([args, domain])
                product_ids = list(self._search(domain, limit=limit, access_rights_uid=name_get_uid))
            if not product_ids and operator in positive_operators:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    product_ids = list(self._search([('default_code', '=', res.group(2))] + args, limit=limit, access_rights_uid=name_get_uid))
            if product_ids:
                return product_ids
            return super(ProductTemplate, self)._name_search(name=name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    burden_percent = fields.Float(string='Burden %', default=lambda s: s.default_burden_percent())
    new_products = fields.One2many('product.superseded', 'old_product',
                                   string="New Product")
    superseded = fields.One2many('product.superseded', 'product_child_id',
                                 string="Supersedes")
    cost = fields.Float(compute='compute_sale_burden', string="Working Cost", digits='Product Price')
    sale_uoms = fields.Many2many('uom.uom', 'product_uom_rel', 'product_id', 'uom_id', string='Sale UOMS')
    vendor_id = fields.Many2one('res.partner', compute='compute_product_vendor', string="Vendor", store=True)
    uom_standard_prices = fields.One2many('product.standard.price', 'product_id', string="UOM STD Prices")

    is_base_user = fields.Boolean(string='Below Minimum Quantity', compute='compute_is_base_user')
    is_bel_min_qty = fields.Boolean(string='Below Minimum Quantity', compute='compute_qty_status', search='_search_bel_min_qty')
    is_bel_crit_qty = fields.Boolean(string='Below Critical Quantity', compute='compute_qty_status', search='_search_bel_crit_qty')
    is_abv_max_qty = fields.Boolean(string='Above Max Quantity', compute='compute_qty_status', search='_search_abv_max_qty')
    # storage_contract_account_id = fields.Many2one('account.account', company_dependent=True,
    #                                               string="Storage Contract Income Account",
    #                                               domain=[('deprecated', '=', False)])
    standard_price_date_lock = fields.Date(string='Standard Price Lock Date')
    product_addons_list = fields.Many2many('product.product', 'product_addons_product_rel', 'product_id',
                                           'addon_product_id', string="Addons Product")
    need_sub_product = fields.Boolean(string='Need Sub-Products')
    similar_product_ids = fields.Many2many('product.product', 'product_similar_product_rel', 'product_id',
                                           'similar_product_id', string="Similar Products")
    count_in_uom = fields.Integer(string='Count in One Unit')
    volume = fields.Float('Volume', help="The volume in m3.", copy=False)
    weight = fields.Float(
        'Weight', digits='Stock Weight',
        help="Weight of the product, packaging not included. The unit of measure can be changed in the general settings",
        copy=False)
    lst_from_std_price = fields.Float(
        'Standard Price', compute='_compute_lst_price_std_price',
        digits='Product Price')

    def action_open_quants(self):
        # Override to make the button readonly for non-inventory users.
        if not self.env.user.has_group('price_paper.group_update_product_on_hand_qty'):
            return {}
        return super().action_open_quants()

    def compute_is_base_user(self):
        #domain to clone the qty on hand button for non-inventory users
        for rec in self:
            rec.is_base_user = False
            if not self.env.user.has_group('stock.group_stock_user') and self.env.user.has_group('base.group_user'):
                rec.is_base_user = True

    def action_view_sales(self):
        """
        Overridden to include superseded product's sale quantity in sale analysis report
        :return: Sale analysis report action
        """
        action = self.env["ir.actions.actions"]._for_xml_id("sale.report_all_channels_sales_action")
        product_ids = self.ids + self.superseded.mapped('old_product').ids
        action['domain'] = [('product_id', 'in', product_ids)]
        action['context'] = {
            'pivot_measures': ['product_uom_qty'],
            'active_id': self._context.get('active_id'),
            'search_default_last_year': 1,
            'search_default_current_month': 1,
            'active_model': 'sale.report',
            'time_ranges': {'field': 'date', 'range': 'last_365_days'},
        }
        return action


    #over ride to not setting uom_po_id
    @api.onchange('uom_id')
    def _onchange_uom_id(self):
        pass
        # if self.uom_id:
        #     self.uom_po_id = self.uom_id.id

    def _compute_lst_price_std_price(self):
        for product in self:
            price = product.uom_standard_prices.filtered(lambda r: r.uom_id == product.uom_id)
            product.lst_from_std_price = price and price[0].price or 0

    @api.model
    def default_burden_percent(self):
        if self.env.user.company_id and self.env.user.company_id.burden_percent:
            return self.env.user.company_id.burden_percent
        return 0

    def copy(self, default=None):
        res = super(ProductProduct, self).copy(default)
        res.with_context(from_copy=True)._check_weight_and_volume()
        if not self._context.get('from_change_uom'):
            res.standard_price = self.standard_price
            # Duplicate price_list line
            for line in self.env['customer.product.price'].search([('product_id', '=', self.id)]):
                line.copy(default={'product_id': res.id})
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if not self.env.user.has_group('stock.group_stock_manager'):
            doc = etree.XML(res['arch'])
            if view_type == 'form':
                nodes = doc.xpath("//notebook//page[@name='superseded']//field[@name='superseded']")
                for node in nodes:
                    node.set('readonly', '1')
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers['readonly'] = True
                    node.set("modifiers", json.dumps(modifiers))
                res['arch'] = etree.tostring(doc, encoding='unicode')
                return res
        return res

    @api.depends('qty_available', 'orderpoint_ids.product_max_qty', 'orderpoint_ids.product_min_qty')
    def compute_qty_status(self):
        for product in self:
            if product.qty_available > product.reordering_max_qty:
                product.is_abv_max_qty = True
            else:
                product.is_abv_max_qty = False

            if product.qty_available < product.reordering_min_qty:
                product.is_bel_min_qty = True
            else:
                product.is_bel_min_qty = False

            crit_config = float(self.env['ir.config_parameter'].sudo().get_param('price_paper.bel_critical_config'))

            if product.qty_available < (product.reordering_min_qty * (crit_config / 100)):
                product.is_bel_crit_qty = True
            else:
                product.is_bel_crit_qty = False

    def _search_bel_min_qty(self, operator, value):
        return self._search_product_quantity_levels(operator, value, 'is_bel_min_qty')

    def _search_bel_crit_qty(self, operator, value):
        return self._search_product_quantity_levels(operator, value, 'is_bel_crit_qty')

    def _search_abv_max_qty(self, operator, value):
        return self._search_product_quantity_levels(operator, value, 'is_abv_max_qty')

    def _search_product_quantity_levels(self, operator, value, field):
        if field not in ('is_bel_min_qty', 'is_bel_crit_qty', 'is_abv_max_qty'):
            raise UserError(_('Invalid domain left operand %s') % field)
        if operator not in ('<', '>', '=', '!=', '<=', '>='):
            raise UserError('Invalid domain operator %s' % operator)
        if not isinstance(value, (float, int)):
            raise UserError('Invalid domain right operand %s' % value)

        ids = []
        for product in self.search([]):
            if OPERATORS[operator](product[field], value):
                ids.append(product.id)
        return [('id', 'in', ids)]

    def toggle_active(self):
        """ remove superseded if there is a child product with superseded set while unarchiving,
        archive reordering rules before archiving product
        """
        for product in self:
            if product.qty_available > 0 and product.active:
                raise ValidationError("Can't archive product with inventory on hand")
            if product.active:
                self.env['product.superseded'].search([('old_product', '=', product.id)]).unlink()
        return super(ProductProduct, self).toggle_active()

    def write(self, vals):
        """
        override to update the customer product price when
        lst_price or burden_percent changes
        """
        # TODO Update price_list when standard price change
        for product in self:
            if 'standard_price' in vals and self.env.context.get('disable_auto_svl'):
                vals.pop('standard_price')
            if 'standard_price' in vals:
                log_vals = {
                    'change_date': fields.Datetime.now(),
                    'type': 'cost',
                    'old_price': product.standard_price,
                    'new_price': vals.get('standard_price'),
                    'user_id': self.env.user.id,
                    'uom_id': product.uom_id.id,
                    'price_from': 'manual',
                    'product_id': product.id
                }
                if self._context.get('user', False):
                    log_vals['user_id'] = self._context.get('user', False)
                if self._context.get('cost_cron', False):
                    log_vals['price_from'] = 'cost_cron'
                self.env['product.price.log'].create(log_vals)
            if 'burden_percent' in vals:
                log_vals = {
                    'change_date': fields.Datetime.now(),
                    'type': 'burden',
                    'old_price': product.burden_percent,
                    'new_price': vals.get('burden_percent'),
                    'user_id': self.env.user.id,
                    'uom_id': product.uom_id.id,
                    'price_from': 'manual',
                    'product_id': product.id
                }
                if self._context.get('user', False):
                    log_vals['user_id'] = self._context.get('user', False)
                if self._context.get('cost_cron', False):
                    log_vals['price_from'] = 'cost_cron'
                self.env['product.price.log'].create(log_vals)
            if 'active' in vals and not vals.get('active'):
                if product.qty_available > 0:
                    raise ValidationError(_("Can't archive product with inventory on hand"))

            if vals.get('burden_percent') or vals.get('standard_price'):
                for rec in product.uom_standard_prices:
                    if rec.cost > rec.price:
                        rec.price = rec.cost

        return super(ProductProduct, self).write(vals)

    @api.model
    def create(self, vals):
        res = super(ProductProduct, self).create(vals)
        if 'standard_price' in vals:
            log_vals = {
                'change_date': fields.Datetime.now(),
                'type': 'cost',
                'new_price': vals.get('standard_price'),
                'user_id': self.env.user.id,
                'uom_id': res.uom_id.id,
                'product_id': res.id
            }
            if self._context.get('user', False):
                log_vals['user_id'] = self._context.get('user', False)
            self.env['product.price.log'].create(log_vals)
        if 'burden_percent' in vals:
            log_vals = {
                'change_date': fields.Datetime.now(),
                'type': 'burden',
                'new_price': vals.get('burden_percent'),
                'user_id': self.env.user.id,
                'uom_id': res.uom_id.id,
                'product_id': res.id
            }
            if self._context.get('user', False):
                log_vals['user_id'] = self._context.get('user', False)
            self.env['product.price.log'].create(log_vals)
        return res

    def name_get(self):
        res = super(ProductProduct, self).name_get()
        if not self._context.get('show_uom_name', False):
            return res
        result = []
        for rec in res:
            name = self.env['product.product'].browse(rec[0]).uom_id.name or ''
            result.append((rec[0], rec[1]+'_'+name))

        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        override to display the superseded product when
        default code of archived product is entered.
        """
        if name:
            active_products = self.env['product.product'].search([('default_code', 'ilike', name)])
            old_products = self.env['product.product'].search([('default_code', 'ilike', name), ('active', '=', False)])
            if old_products and not active_products:
                new_products = self.env['product.product'].search([('superseded.old_product', 'in', old_products.ids)])
                # if active_products:
                #     new_products = active_products + new_products
                if new_products:
                    return new_products.name_get()
        return super(ProductProduct, self).name_search(name=name, args=args, operator=operator, limit=limit)

    @api.depends('seller_ids','seller_ids.sequence')
    def compute_product_vendor(self):
        """
        Compute vendor of the product
        """
        for rec in self:
            vendors_sorted = rec.seller_ids and rec.seller_ids.sorted('sequence')
            rec.vendor_id = vendors_sorted and vendors_sorted[0].name.id or False

    @api.depends('standard_price', 'burden_percent')
    def compute_sale_burden(self):
        """
        Compute cost price by adding burden percentage
        """
        for rec in self:
            burden_factor = rec.burden_percent / 100
            burden = rec.standard_price * burden_factor
            if burden:
                rec.cost = burden + rec.standard_price
            else:
                rec.cost = rec.standard_price

    @api.onchange('sale_uoms')
    def onchange_sale_uoms(self):
        """
        """
        return {'domain': {
            'uom_id': ([('id', 'in', self.sale_uoms.ids)]),
            'uom_po_id': ([('id', 'in', self.sale_uoms.ids)])
        }}

    @api.constrains('weight', 'volume')
    def _check_weight_and_volume(self):
        for rec in self:
            if self._context.get('from_change_uom') and not self._context.get('from_copy', False):
                continue
            if rec.weight <= 0 and rec.type == 'product':
                raise ValidationError('Weight should be greater than Zero')
            if rec.volume <= 0 and rec.type == 'product':
                raise ValidationError('Volume should be greater than Zero')

    def _compute_sales_count(self):
        """
        Overridden to include superseded products sale quantity in product sale_count
        :return: sale_count
        """
        r = {}
        self.sales_count = 0
        if not self.user_has_groups('sales_team.group_sale_salesman'):
            return r
        date_from = fields.Datetime.to_string(fields.datetime.combine(fields.datetime.now() - timedelta(days=365),
                                                                      time.min))

        done_states = self.env['sale.report']._get_done_states()
        domain = [
            ('state', 'in', done_states),
            ('product_id', 'in', self.ids),
            ('date', '>=', date_from),
        ]
        for group in self.env['sale.report'].read_group(domain, ['product_id', 'product_uom_qty'], ['product_id']):
            r[group['product_id'][0]] = group['product_uom_qty']
        for product in self:
            if not product.id:
                product.sales_count = 0.0
                continue
            product.sales_count = float_round(r.get(product.id, 0), precision_rounding=product.uom_id.rounding) + sum(product.superseded.old_product.mapped('sales_count'))
        return r

    @api.onchange('lst_price')
    def _set_product_lst_price(self):
        """To resolve the audit log code issue, I overrode the method.
        The superclass method calls "write()" instead of update, but the new object lacks an ID to write, causing the audit log methods to fail."""
        for product in self:
            if self._context.get('uom'):
                value = self.env['uom.uom'].browse(self._context['uom'])._compute_price(product.lst_price, product.uom_id)
            else:
                value = product.lst_price
            value -= product.price_extra
            product.update({'list_price': value})



class ProductUom(models.Model):
    _inherit = "uom.uom"

    product_ids = fields.Many2many('product.product', 'product_uom_rel', 'uom_id', 'product_id', string="Products")


class ProductSuperseded(models.Model):
    _name = 'product.superseded'
    _description = 'Superseded Products'

    old_product = fields.Many2one('product.product', string="Old Product",
                                  domain=[('active', '=', False)], required=True, ondelete='cascade')
    product_child_id = fields.Many2one('product.product', string="New Product",
                                       readonly=True,required=False)

    @api.constrains('old_product', 'product_child_id')
    def check_duplicates(self):
        result = self.search([
            ('old_product', '=', self.old_product.id),
            ('product_child_id', '=', self.product_child_id.id),
            ('id', '!=', self.id)
        ])
        if result:
            raise UserError('Duplicate entry in superseded')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
