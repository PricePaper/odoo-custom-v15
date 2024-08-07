from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    points_to_redeem = fields.Integer(string="Points", copy=False, readonly=True)

    '''For Redeem Loyalty button'''

    def get_total_points(self):
        order = self.sudo()
          
        total_points = 0
        if order.partner_id.is_loyalty_eligible:
            loyalty_programs = self.env['website.loyalty.program'].sudo().search([
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
        
        


    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if order.partner_id.is_loyalty_eligible:

                # Query loyalty programs based on the source (website or not)
                if order.website_id:
                    loyalty_programs = self.env['website.loyalty.program'].search([
                        ('company_id', '=', order.company_id.id),
                        ('active', '=', True),
                        ('available_on_website', '=', True)
                    ], order='minimum_order desc')
                else:
                    loyalty_programs = self.env['website.loyalty.program'].search([
                        ('company_id', '=', order.company_id.id),
                        ('active', '=', True)
                    ], order='minimum_order desc')

                category_programs = loyalty_programs.filtered(lambda p: p.only_category_ids)
                print("categorrrrry = ", category_programs)
                no_category_programs = loyalty_programs.filtered(lambda p: not p.only_category_ids)
                print("no category = ", no_category_programs)

                applied_programs = {}

                for line in order.order_line:
                    product = line.product_id
                    total_amount = line.price_subtotal
                    applied_program = None

                    # Check if the product belongs to a specific loyalty program with categories
                    for loyalty_program in category_programs:
                        if any(category.id in loyalty_program.only_category_ids.ids for category in
                               product.public_categ_ids):
                            applied_program = loyalty_program
                            break

                    # If no specific category program is found, use the no-category program
                    if not applied_program and no_category_programs:
                        applied_program = no_category_programs[0]

                    if applied_program:
                        if applied_program.id not in applied_programs:
                            applied_programs[applied_program.id] = {'program': applied_program, 'total_amount': 0}
                        applied_programs[applied_program.id]['total_amount'] += total_amount
                transaction_created = False
                points_to_redeem = order.points_to_redeem

                for program_data in applied_programs.values():
                    loyalty_program = program_data['program']
                    total_amount = program_data['total_amount']

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

                        customer_rank = order.partner_id.customer_ranks
                        tier_customer = self.env['website.loyalty.tier.customer'].search(
                            [('customer_rank', '=', customer_rank)], limit=1)
                        tier_name = tier_customer.tier_id.name if tier_customer and tier_customer.tier_id else ""
                        transaction = self.env['loyalty.transaction'].search([
                            ('order_id', '=', order.id),
                            ('state', '=', 'draft')
                        ], limit=1)
                        if transaction:
                            transaction.write({
                                'credit': final_credit,
                                # 'debit': points_to_redeem if points_to_redeem else 0,
                                'loyalty_program_id': loyalty_program.id,
                                'tiers_id': tier_name,
                                'state': 'pending'
                            })
                        else:

                            print(f"Creating loyalty transaction for order {order.id} with program {loyalty_program.name}")
                            self.env['loyalty.transaction'].create({
                                'date': fields.Date.today(),
                                'credit': final_credit,
                                'debit': points_to_redeem if points_to_redeem else 0,
                                'order_id': order.id,
                                'partner_id': order.partner_id.id,
                                'loyalty_program_id': loyalty_program.id,
                                'tiers_id': tier_name,
                                'state': 'pending'
                            })
                        transaction_created = True


                    else:
                        print(
                            f"Total amount {total_amount} is less than the minimum order {loyalty_program.minimum_order} for program {loyalty_program.name}")
                if not transaction_created:
                    order.partner_id.no_transaction_debit = points_to_redeem if points_to_redeem else 0
                else:
                    order.partner_id.no_transaction_debit = 0

        return res

    # redemption_product_present = any(line.is_redemption_product for line in order.order_line)
    # print("redemption product", redemption_product_present)

    def redeem_points(self, points_to_redeem):
        self.ensure_one()
        result = {
            'status': False,
            'error_message': False,
            'amount': 0,
            'points': points_to_redeem
        }
        if self.points_to_redeem:
            result['error_message'] = "You have already redeemed points for this order."
            return result

        # Check if the customer is eligible for loyalty redemption
        if not self.partner_id.is_loyalty_eligible:
            result['error_message'] = "Partner is not eligible for loyalty."
            return result

        # Check if the customer has enough confirmed points
        if self.partner_id.total_confirm_points < points_to_redeem:
            result['error_message'] = f"Partner has only {self.partner_id.total_confirm_points} confirmed points."
            return result

        # Fetch the active redemption rule
        redeem_rule = self.env['website.loyalty.redeem.rules'].search([('active', '=', True)], limit=1)
        if not redeem_rule:
            result['error_message'] = "No active redemption rule found."
            return result

        # Check if the order total is greater than or equal to minimum_order_redeem
        if self.amount_total < redeem_rule.minimum_order_redeem:
            result['error_message'] = "Order total is less than the minimum order required for redeeming points."
            return result

        # Validate the redemption points
        if points_to_redeem > redeem_rule.maximum_points_redeem:
            result['error_message'] = "Points exceed maximum points redeemable."
            return result

        # Redeem points using the redemption rule
        redeem_result = redeem_rule.redeem_points(self, points_to_redeem)

        result['status'] = True
        result['amount'] = redeem_result['amount']
        result['points']=redeem_result['points']
        if result['status']:
            self.points_to_redeem = redeem_result['points']
            self.env['loyalty.transaction'].create({
                'date': fields.Date.today(),
                'debit': self.points_to_redeem,
                'order_id': self.id,
                'partner_id': self.partner_id.id,
                'state': 'draft'
            })

        return result

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        for order in self:
            transactions = self.env['loyalty.transaction'].search([('order_id', '=', order.id)])
            for transaction in transactions:
                transaction.write({'state': 'cancel'})
        return res
