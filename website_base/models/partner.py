from odoo import api,models,fields
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_is_zero, float_round
from datetime import datetime, date

class ResPartner(models.Model):
    _inherit='res.partner'

    def get_product_price(self,product_ids):
           
        """
        Fetch unit price from the relevant pricelist of partner
        if product is not found in any pricelis_uot,set
        product price as Standard price of product
        """
        prices={}
        
        for product_id in product_ids:

            partner_com = self
            product_id  =self.env['product.product'].browse([int(product_id)])
            prices_all = self.env['customer.product.price']
            for rec in partner_com.customer_pricelist_ids:
                if not rec.pricelist_id.expiry_date or rec.pricelist_id.expiry_date >= date.today():
                    prices_all |= rec.pricelist_id.customer_product_price_ids

            prices_all = prices_all.filtered(lambda r: r.product_id.id == product_id.id and (not r.partner_id or r.partner_id.id == partner_com.id))
            product_price = 0.0
            price_from = False
            msg = ''
            uom_price = []
            standard_prices = {}
            for price_rec in prices_all:

                if price_rec.pricelist_id.type == 'customer' and not price_rec.partner_id and prices_all.filtered(lambda r: r.partner_id):
                    continue

                
                product_price = price_rec.price
                price_dict  ={'uom':price_rec.product_uom.id,'price':float_round(product_price,precision_digits=2)}
                uom_price.append(price_dict)
                
            
            if product_id :
                
                uom_price_main = product_id.uom_standard_prices
                if uom_price_main:
                    standard_prices = [{'uom':r.uom_id.id,'price':float_round(r.price,precision_digits=2)} for r in  uom_price_main]

                msg = "Unit Price for this product is not found in any pricelists, fetching the unit price as product standard price."

            prices[product_id.id] = [{"customer_prices":uom_price,"standart_prices":standard_prices}]
        
        return prices


