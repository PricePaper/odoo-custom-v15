from odoo import fields, models, api, _
from odoo.exceptions import UserError



class StockPicking(models.Model):
    _inherit = 'stock.picking'


    def validate_multiple_delivery(self):
        for rec in self:
            if rec.state != 'in_transit' and not rec.rma_id and not rec.purchase_id:
                raise UserError(_(
                    "Some of the selected Delivery order is not in transit state"))
            rec.button_validate()
        return self
