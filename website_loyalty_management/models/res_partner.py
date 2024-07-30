from odoo import fields, models, api


class Partner(models.Model):
    _inherit = 'res.partner'

    is_loyalty_eligible = fields.Boolean(string="Eligible for Loyalty", default=False)
    loyalty_transaction_ids = fields.One2many('loyalty.transaction', 'partner_id', string='Loyalty Transactions',readonly=True)
    total_loyalty_points = fields.Integer(string="Total loyalty points", compute='_compute_total_loyalty_points',
                                          store=True)
    loyal_programs = fields.Many2one('website.loyalty.program', string="Loyalty programs")
    customer_ranks = fields.Char(string="Customer Rank")
    loyalty_transaction_count = fields.Integer(string="Loyalty Transaction Count",
                                               compute='_compute_loyalty_transaction_count', store=True)
    total_pending_points = fields.Integer(string="Pending Points", compute='_compute_loyalty_points')
    total_confirm_points = fields.Integer(string="Confirm Points", compute='_compute_loyalty_points')
    partenr_tier = fields.Char(string='Partner Tier',compute='_compute_partner_tier')

    @api.depends('rnk_lst_3_mon')
    def _compute_partner_tier(self):
        for rec in self:
            tier = self.env['website.loyalty.tier.customer'].sudo().search([('customer_rank','=',rec.rnk_lst_3_mon)],limit=1)
            if tier:
                rec.partenr_tier = tier.tier_id.name
            else:
                rec.partner_tier = ''

    # redeem_rule = fields.Many2one('website.loyalty.redeem.rules', string="Active redeem rules")

    @api.depends('loyalty_transaction_ids.credit', 'loyalty_transaction_ids.debit')
    def _compute_total_loyalty_points(self):
        for partner in self:
            total_credit = sum(transaction.credit for transaction in partner.loyalty_transaction_ids)
            total_debit = sum(transaction.debit for transaction in partner.loyalty_transaction_ids)
            partner.total_loyalty_points = total_credit - total_debit

    @api.depends('loyalty_transaction_ids')
    def _compute_loyalty_transaction_count(self):
        for partner in self:
            partner.loyalty_transaction_count = len(partner.loyalty_transaction_ids)

    @api.depends('loyalty_transaction_ids.state', 'loyalty_transaction_ids.credit', 'loyalty_transaction_ids.debit')
    def _compute_loyalty_points(self):
        for partner in self:
            pending_points = 0
            confirm_points = 0
            for transaction in partner.loyalty_transaction_ids:
                if transaction.state == 'pending':
                    pending_points += transaction.credit - transaction.debit
                elif transaction.state == 'confirmed':
                    confirm_points += transaction.credit - transaction.debit
            partner.total_pending_points = pending_points
            partner.total_confirm_points = confirm_points
