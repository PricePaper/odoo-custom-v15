from odoo import models,fields,api
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    is_redemption_product = fields.Boolean(string="Is redemption product", readonly=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.is_redemption_product:
            self.product_id = self._origin.product_id
            raise ValidationError("You cannot edit the redemption product.")

    @api.onchange('product_uom_qty', 'price_unit')
    def _onchange_redemption_product_details(self):
        if self.is_redemption_product:
            if 'product_uom_qty' in self._origin:
                self.product_uom_qty = self._origin.product_uom_qty
            if 'price_unit' in self._origin:
                self.price_unit = self._origin.price_unit
            raise ValidationError("You cannot edit the redemption product details.")

    def _is_not_sellable_line(self):
        print("entered into it")
        if self.is_redemption_product:
            return True
        return super(SaleOrderLine, self)._is_not_sellable_line()

    # def unlink(self):
    #     # Prevent deletion of redemption products
    #     if any(line.is_redemption_product for line in self):
    #         raise ValidationError("You cannot delete the redemption product.")
    #     return super(SaleOrderLine, self).unlink()







