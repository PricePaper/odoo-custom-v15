from odoo import http
from odoo.http import request


class WebsiteSaleLoyalty(http.Controller):

    @http.route('/shop/redeem_loyalty', type='json', auth="user", website=True)
    def redeem_loyalty(self, order_id, points_to_redeem):
        print(f"Order ID: {order_id}, Points to Redeem: {points_to_redeem}")

        # Create the wizard with the order_id in the context
        wizard = request.env['redeem.loyalty.wizard'].with_context(from_website=True, active_id=order_id).create({
            'points_to_redeem': points_to_redeem
        })

        # Call the action_redeem method with order_id as a parameter
        result = wizard.action_redeem(order_id=order_id)
        print(f"Result: {result}")

        if result['status']:
            return {'status': 'success', 'message': 'Points redeemed successfully.'}
        else:
            return {'status': 'error', 'message': result['error_message']}
