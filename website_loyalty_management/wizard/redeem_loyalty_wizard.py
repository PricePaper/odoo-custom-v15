from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class RedeemLoyaltyWizard(models.TransientModel):
    _name = 'redeem.loyalty.wizard'
    _description = 'Redeem Loyalty Points Wizard'

    points_to_redeem = fields.Integer(string="Points to Redeem", required=True)

    # def action_redeem(self):
    #     order_id = self.env.context.get('active_id')
    #     order = self.env['sale.order'].browse(order_id)
    #     result = order.redeem_points(self.points_to_redeem)
    #     if result['status']:
    #         order.points_to_redeem = self.points_to_redeem
    #     return result

    @api.constrains('points_to_redeem')
    def _check_points_to_redeem(self):
        for wizard in self:
            if wizard.points_to_redeem < 0:
                raise ValidationError("The points to redeem cannot be negative.")

    def action_redeem(self, order_id=None):
        result = {
            'status': False,
            'error_message': '',
            'amount': 0,
            'points': self.points_to_redeem
        }

        if not order_id:
            order_id = self.env.context.get('active_id')
        order = self.env['sale.order'].browse(order_id)

        # Determine the context: website or backend
        is_website_request = self.env.context.get('from_website', False)

        if order.points_to_redeem:
            if is_website_request:
                result['error_message'] = "You have already redeemed points for this order."
                return result
            else:
                raise ValidationError("You have already redeemed points for this order.")

        redeem_rule = self.env['website.loyalty.redeem.rules'].search([('active', '=', True)], limit=1)
        if not order.partner_id.is_loyalty_eligible:
            if is_website_request:
                result['error_message'] = "Partner is not eligible for loyalty."
                return result
            else:
                raise ValidationError("Partner is not eligible for loyalty.")

        if not redeem_rule:
            if is_website_request:
                result['error_message'] = "No active redemption rule found."
                return result
            else:
                raise ValidationError("No active redemption rule found.")

        if order.partner_id.total_confirm_points < self.points_to_redeem:
            if is_website_request:
                result['error_message'] = f"Partner has only {order.partner_id.total_confirm_points} confirmed points."
                return result
            else:
                raise ValidationError(f"Partner has only {order.partner_id.total_confirm_points} confirmed points.")

        eligible_for_redemption = any(
            line.price_subtotal >= redeem_rule.minimum_order_redeem for line in order.order_line)
        if not eligible_for_redemption:
            if is_website_request:
                result['error_message'] = "Order total is less than the minimum order required for redeeming points."
                return result
            else:
                raise ValidationError("Order total is less than the minimum order required for redeeming points.")

        if self.points_to_redeem > redeem_rule.maximum_points_redeem:
            if is_website_request:
                result['error_message'] = "Points exceed maximum points redeemable."
                return result
            else:
                raise ValidationError("Points exceed maximum points redeemable.")

        # Proceed with redeeming points
        redeem_result = order.redeem_points(self.points_to_redeem)
        if redeem_result['status']:
            order.points_to_redeem = self.points_to_redeem
            self.env['loyalty.transaction'].create({
                'date': fields.Date.today(),
                'debit': self.points_to_redeem,
                'order_id': order.id,
                'partner_id': order.partner_id.id,
                'state': 'draft'
            })
            result['status'] = True
            result['amount'] = redeem_result['amount']
            result['points'] = redeem_result['points']

        return result
