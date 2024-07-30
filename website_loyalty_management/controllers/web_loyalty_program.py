from odoo import http
from odoo.http import request

class LoyaltyController(http.Controller):

    @http.route('/my/loyalty', type='http', auth='user', website=True)
    def loyalty_page(self, **kwargs):
        loyalty_programs = request.env['website.loyalty.program'].search([])  # Fetch all loyalty programs
        values = {
            'loyalty_programs': loyalty_programs
        }
        return request.render('website_loyalty_management.loyalty_template', values)
