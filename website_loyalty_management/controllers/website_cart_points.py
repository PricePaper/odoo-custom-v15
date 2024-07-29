from odoo import http, fields
from odoo.http import request
from werkzeug.exceptions import Forbidden, NotFound
from odoo.addons.website_sale.controllers.main import WebsiteSale

'''controller for setting credit points according to loyalty programs
only users who's eligible for loyalty program and "website" is enabled  will be credited with the points'''


class WebsiteSale(WebsiteSale):

    @http.route(['/shop/cart'], type='http', auth="public", website=True, sitemap=False)
    def cart(self, access_token=None, revive='', **post):
        order = request.website.sale_get_order()
        if order and order.state != 'draft':
            request.session['sale_order_id'] = None
            order = request.website.sale_get_order()
        values = {}
        if access_token:
            abandoned_order = request.env['sale.order'].sudo().search([('access_token', '=', access_token)], limit=1)
            if not abandoned_order:
                raise NotFound()
            if abandoned_order.state != 'draft':
                values.update({'abandoned_proceed': True})
            elif revive == 'squash' or (revive == 'merge' and not request.session.get('sale_order_id')):
                request.session['sale_order_id'] = abandoned_order.id
                return request.redirect('/shop/cart')
            elif revive == 'merge':
                abandoned_order.order_line.write({'order_id': request.session['sale_order_id']})
                abandoned_order.action_cancel()
            elif abandoned_order.id != request.session.get('sale_order_id'):
                values.update({'access_token': abandoned_order.access_token})

        values.update({
            'website_sale_order': order,
            'date': fields.Date.today(),
            'suggested_products': [],
        })
        if order:
            order.order_line.filtered(lambda l: not l.product_id.active).unlink()
            _order = order
            if not request.env.context.get('pricelist'):
                _order = order.with_context(pricelist=order.pricelist_id.id)
            values['suggested_products'] = _order._cart_accessories()

            # Calculate loyalty points for the current cart
            total_credit_points = self._calculate_loyalty_points(order) or 0
            values['total_credit_points'] = total_credit_points

        if post.get('type') == 'popover':
            return request.render("website_sale.cart_popover", values, headers={'Cache-Control': 'no-cache'})

        return request.render("website_sale.cart", values)

    def _calculate_loyalty_points(self, order):
        total_credit = 0
        if order.partner_id.is_loyalty_eligible:
            loyalty_programs = request.env['website.loyalty.program'].search([
                ('company_id', '=', order.company_id.id),
                ('active', '=', True),
                ('available_on_website', '=', True)  # Ensure the program is available on the website
            ], order='minimum_order desc')

            for loyalty_program in loyalty_programs:
                total_amount = 0
                for line in order.order_line:
                    product = line.product_id
                    if any(category.id in loyalty_program.only_category_ids.ids for category in
                           product.public_categ_ids):
                        total_amount += line.price_subtotal

                if total_amount >= loyalty_program.minimum_order:
                    base_credit = (loyalty_program.no_of_points / loyalty_program.dollar_spent) * total_amount
                    if base_credit > loyalty_program.maximum_points:
                        base_credit = loyalty_program.maximum_points
                    else:
                        base_credit = round(base_credit)

                    highest_order_value = 0
                    related_bonus_percentage = 0
                    for rule in loyalty_program.bonus_rule_ids:
                        if total_amount >= rule.order_value and rule.order_value > highest_order_value:
                            highest_order_value = rule.order_value
                            related_bonus_percentage = rule.bonus_percentage

                    bonus_points = (related_bonus_percentage / 100) * base_credit if highest_order_value > 0 else 0
                    final_credit = base_credit + bonus_points
                    total_credit += final_credit
        return total_credit
