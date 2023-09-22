# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductSkuReference(models.Model):
    _name = "product.sku.reference"
    _description = "Product SKU Reference"
    _inherit = ['mail.thread']

    product_id = fields.Many2one('product.product', string='Product', required=True)
    competitor_sku = fields.Char(string='Competitor SKU')
    competitor_desc = fields.Char(string='Competitor description')
    website_link = fields.Char(string='URL')
    qty_in_uom = fields.Float(string='Units in UOM')
    competitor = fields.Selection(related='web_config.competitor', string='Competitors')
    web_config = fields.Many2one('website.scraping.cofig', string='Competitor')
    scheduled_ids = fields.One2many('price.fetch.schedule', 'product_sku_ref_id', string='Scheduled Price Fetches')
    in_exception = fields.Boolean(string='Exception', default=False)
    is_unavailable = fields.Boolean(string='Unavailable', default=False)


    @api.constrains('competitor_sku', 'web_config')
    def check_total_amount(self):
        for sku in self:
            if sku.competitor_sku and sku.web_config:
                sku_exist = self.env['product.sku.reference'].search([('competitor_sku', '=', sku.competitor_sku), ('web_config', '=', sku.web_config.id), ('id', '!=', sku.id)])
                if sku_exist:
                    raise ValidationError('Competitor sku already exist')

    @api.depends('product_id', 'competitor')
    def name_get(self):
        result = []
        for record in self:
            name = "%s_%s" % (record.product_id and record.product_id.name,
                              record.competitor and dict(self._fields['competitor'].selection(record)).get(
                                  record.competitor) or '')
            result.append((record.id, name))
        return result


    def schedule_price_update(self):
        """
        creates a scheduled task in the system
        """
        for rec in self:
            if not rec.in_exception:
                self.env['price.fetch.schedule'].create({'product_sku_ref_id': rec.id})

    def mark_exception_fixed(self):
        for rec in self:
            rec.in_exception = False
            rec.is_unavailable = False
            rec.message_post(body="Exception Removed")

    @api.model
    def log_exception_error(self, ref_id, except_string="Exception Error"):
        ref_obj = self.env['product.sku.reference'].browse(ref_id)
        if except_string == 'Temporarily unavailable':
            ref_obj.is_unavailable = True
        ref_obj.in_exception = True
        ref_obj.message_post(body=except_string)
        return True


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
