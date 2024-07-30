from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    '''For Redeem Loyalty button'''

    def get_total_points(self):
        order = self
          
        total_points = 0
        if order.partner_id.is_loyalty_eligible:
            loyalty_programs = self.env['website.loyalty.program'].search([
                ('company_id', '=', order.company_id.id),
                ('active', '=', True)
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

                    # Lookup tier based on customer rank
                    customer_rank = order.partner_id.customer_ranks
                    tier_customer = self.env['website.loyalty.tier.customer'].search(
                        [('customer_rank', '=', customer_rank)], limit=1)
                    tier_name = tier_customer.tier_id.name if tier_customer and tier_customer.tier_id else ""
                    total_points+=final_credit
        return total_points
        
        


    def action_redeem_loyalty(self):
        for order in self:
            if order.partner_id.company_type == 'company':
                order.partner_id.is_loyalty_eligible = True
                print("Loyalty program is active for this customer.")
                order.message_post(body="Loyalty program is active for this customer.")
            else:
                order.partner_id.is_loyalty_eligible = False
                print("Loyalty program is not active for this customer.")
                order.message_post(body="Loyalty program is not active for this customer.")

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if order.partner_id.is_loyalty_eligible:
                loyalty_programs = self.env['website.loyalty.program'].search([
                    ('company_id', '=', order.company_id.id),
                    ('active', '=', True)
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

                        # Lookup tier based on customer rank
                        customer_rank = order.partner_id.customer_ranks
                        tier_customer = self.env['website.loyalty.tier.customer'].search(
                            [('customer_rank', '=', customer_rank)], limit=1)
                        tier_name = tier_customer.tier_id.name if tier_customer and tier_customer.tier_id else ""

                        self.env['loyalty.transaction'].create({
                            'date': fields.Date.today(),
                            'credit': final_credit,
                            'debit': 0,
                            'order_id': order.id,
                            'partner_id': order.partner_id.id,
                            'loyalty_program_id': loyalty_program.id,
                            'tiers_id': tier_name,  # Store the tier name directly
                            'state': 'pending'
                        })
        return res
