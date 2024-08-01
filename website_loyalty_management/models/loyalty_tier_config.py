from odoo import api, fields, models

from odoo import models, fields
from odoo.exceptions import ValidationError


class LoyaltyTransaction(models.Model):
    _name = 'website.loyalty.tier'
    _description = 'Loyalty Tier'

    name = fields.Char(string="Tier Name")
    tier_image = fields.Binary(string='Tier Image')
    tier_color = fields.Char(string='Color Code')


    @api.constrains('name')
    def _check_unique_name(self):
        for record in self:
            existing_tier = self.search([
                ('name', '=ilike', record.name),
                ('id', '!=', record.id)
            ])
            if existing_tier:
                raise ValidationError('Tier Name must be unique.')


class WebsiteLoyaltyTierCustomer(models.Model):
    _name = 'website.loyalty.tier.customer'
    _description = 'Loyalty Tier Customer and Configuration'

    _rec_name = 'customer_rank'

    customer_rank = fields.Char(string='Customer Rank')
    tier_id = fields.Many2one('website.loyalty.tier', string='Tiers')

    @api.constrains('customer_rank')
    def _check_unique_custoemr_rank(self):
        for record in self:
            existing_rank = self.search([('id', '!=', record.id), ('customer_rank', '=', record.customer_rank)])
            if existing_rank:
                raise ValidationError("Customer rank already exists it should be unique")

    @api.constrains('tier_id')
    def _check_unique_tier_ids(self):
        for record in self:
            existing_record = self.search([
                ('tier_id', '=', record.tier_id.id),
                ('id', '!=', record.id)
            ])
            if existing_record:
                raise ValidationError(f"The selected tier {record.tier_id.name} is already assigned.")
