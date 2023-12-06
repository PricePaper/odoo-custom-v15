# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CompetitorItems(models.Model):
    _name = "competitor.website.price"
    _description = "Price from competitor's website"

    product_sku_ref_id = fields.Many2one('product.sku.reference', string='Reference')
    item_name = fields.Char(string='Competitor Item Name')
    item_price = fields.Float(string='Competitor Price')
    price = fields.Float(compute='get_price', string='Unit Price')
    competitor_item_uom = fields.Float(string='Competitor Units in UOM', related='product_sku_ref_id.qty_in_uom',
                                       readonly=True)
    update_date = fields.Datetime(string='Updated On')
    product_id = fields.Many2one(related='product_sku_ref_id.product_id', string='Product', readonly=True)
    competitor = fields.Selection(related='product_sku_ref_id.web_config.competitor', string='Competitor')
    active = fields.Boolean(string='Active', default=True)

    @api.depends('item_price')
    def get_price(self):
        """
        Get price from Reference record
        """
        for record in self:
            price = 0.0
            if record.product_sku_ref_id.qty_in_uom:
                price = (record.item_price / record.competitor_item_uom) * record.product_id.ppt_uom_id.factor_inv
            record.price = price

    @api.depends('product_sku_ref_id')
    def name_get(self):
        result = []
        for record in self:
            name = "%s_%s" % (record.product_sku_ref_id and record.product_sku_ref_id.product_id.name,
                              record.product_sku_ref_id and dict(
                                  self.product_sku_ref_id._fields['competitor'].selection(
                                      record.product_sku_ref_id)).get(record.product_sku_ref_id.competitor) or '')
            result.append((record.id, name))
        return result

    @api.model
    def create(self, vals):
        res = super(CompetitorItems, self).create(vals)
        res.update_competitor_pricelist()
        return res

    def update_competitor_pricelist(self):
        """
        Update competitor customer product price with current configuration price
        Add product lines if it is not exist in competitor customer product pricelist section
        """
        for rec in self:
            pricelists = self.env['product.pricelist'].search(
                [('type', '=', 'competitor'), ('competitor_id', '=', rec.product_sku_ref_id.web_config.id)])

            for pricelist in pricelists:
                lines = pricelist.customer_product_price_ids.filtered(lambda p: p.product_id.id == rec.product_id.id)
                price = rec.price + (rec.price * pricelist.competietor_margin / 100)
                for line in lines:
                    if line.price != price or line.product_uom != rec.product_id.ppt_uom_id:
                        line.write({'price': price,
                                    'product_uom': rec.product_id.ppt_uom_id.id,
                                    })
                if not lines:
                    self.env['customer.product.price'].create({'pricelist_id': pricelist.id,
                                                               'product_id': rec.product_id.id,
                                                               'price': price,
                                                               'product_uom': rec.product_id.ppt_uom_id.id,
                                                               })
        return True



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
