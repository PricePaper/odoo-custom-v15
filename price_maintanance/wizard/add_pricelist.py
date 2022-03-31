from odoo import models, fields, api


class AddPricelists(models.TransientModel):
    _name = 'add.pricelist'
    _description = 'Create new pricelists'

    partner_pricelist_line_ids = fields.Many2many('customer.product.price',
                                                  string="Customer Pricelist line")
    def add_pricelist_lines(self):
        partner = self._context.get('record',False)
        pricelist_partner = self.env['res.partner'].browse(partner)
        for rec in self.partner_pricelist_line_ids:
            records = pricelist_partner.partner_pricelist_id.pricelist_id
            records.write({'customer_product_price_ids': [(4, rec.id)]})
