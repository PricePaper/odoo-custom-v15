from odoo import models, fields


class LoyaltyTransaction(models.Model):
    _name = 'loyalty.transaction'
    _description = 'Loyalty Transaction'

    date = fields.Date(string='Date', default=fields.Date.today)
    credit = fields.Float(string='Credit')
    debit = fields.Float(string='Debit')
    loyalty_program_id = fields.Many2one('website.loyalty.program', string='Loyalty Program')
    order_id = fields.Many2one('sale.order', string='Order')
    partner_id = fields.Many2one('res.partner', string='Customer')
    # product_ids = fields.Many2many('product.product', string='Products')
    tiers_id = fields.Char(string='Tier')  # previously many2one field
    state = fields.Selection(selection=[
        ('draft','draft'),
        ('pending', 'pending'),
        ('confirmed', 'confirmed'),
        ('cancel','cancel')], string='State')
