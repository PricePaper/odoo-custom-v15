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

    def action_redeem(self):

        order_id = self.env.context.get('active_id')
        order = self.env['sale.order'].browse(order_id)
        if order.points_to_redeem:
            raise ValidationError("You have already redeemed points for this order.")

        # Fetch the active redemption rule
        redeem_rule = self.env['website.loyalty.redeem.rules'].search([('active', '=', True)], limit=1)
        if not order.partner_id.is_loyalty_eligible:
            raise ValidationError("Partner is not eligible for loyalty.")

        if not redeem_rule:
            raise ValidationError("No active redemption rule found.")
        if order.partner_id.total_confirm_points < self.points_to_redeem:
            raise ValidationError(f"Partner has only {order.partner_id.total_confirm_points} confirmed points.")

        # Check if the order total is greater than or equal to minimum_order_redeem
        if order.amount_total < redeem_rule.minimum_order_redeem:
            raise ValidationError(
                "You have nothing to redeem. Order total is less than the minimum order required for redeeming points.")
        if self.points_to_redeem > redeem_rule.maximum_points_redeem:
            raise ValidationError(
                "Points exceed maximum points redeemable.")

        result = order.redeem_points(self.points_to_redeem)
        if result['status']:
            order.points_to_redeem = self.points_to_redeem
            self.env['loyalty.transaction'].create({
                'date': fields.Date.today(),
                'debit': self.points_to_redeem,
                'order_id': order.id,
                'partner_id': order.partner_id.id,
                'state': 'draft'
            })
            print(f"Redeemed amount: {result['amount']}, Points used: {result['points']}")
        return result
