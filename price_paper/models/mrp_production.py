# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.onchange('product_id')
    def onchange_product(self):
        """ Set Location"""
        if not self.product_id:
            self.location_dest_id = False
        else:
            if self.product_id.property_stock_location:
                self.location_dest_id = self.product_id.property_stock_location.id
            else:
                self.location_dest_id = self._get_default_location_dest_id()


MrpProduction()
