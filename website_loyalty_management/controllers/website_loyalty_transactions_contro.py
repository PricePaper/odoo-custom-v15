from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request
from odoo import http


class CustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super(CustomerPortal, self)._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        if 'loyalty_transaction_count' in counters:
            # Count loyalty transactions directly associated with the logged-in user's partner
            loyalty_transaction_count = request.env['loyalty.transaction'].search_count([
                ('partner_id', '=', partner.id)
            ])
            values['loyalty_transaction_count'] = loyalty_transaction_count

        return values

    @http.route(['/my/loyalty/transactions', '/my/loyalty/transactions/page/<int:page>'], type='http', auth="user",
                website=True)
    def loyalty_transactions(self, page=1, date_begin=None, date_end=None, sortby=None, **kwargs):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        LoyaltyTransaction = request.env['loyalty.transaction']

        domain = [('partner_id', '=', partner.id)]
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        transaction_count = LoyaltyTransaction.search_count(domain)
        pager = request.website.pager(
            url="/my/loyalty/transactions",
            total=transaction_count,
            page=page,
            step=self._items_per_page
        )
        transactions = LoyaltyTransaction.search(domain, order='create_date desc', limit=self._items_per_page,
                                                 offset=pager['offset'])

        values.update({
            'loyalty_transactions': transactions,
            'page_name': 'loyalty_transaction',
            'pager': pager,
            'default_url': '/my/loyalty/transactions',
            'date': date_begin,
            'sortby': sortby,
            'loyalty_transaction_count': transaction_count,
            'total_pending_points': partner.total_pending_points,
            'total_confirm_points': partner.total_confirm_points,
        })
        return request.render("website_loyalty_management.loyalty_transactions_template", values)
