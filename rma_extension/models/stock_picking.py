from odoo import fields, models, api, _
from odoo.exceptions import UserError



class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def validate_multiple_delivery(self, records):
        for rec in records:
            if rec.state != 'in_transit' and not rec.rma_id and not rec.pucrchase_id:
                raise UserError(_(
                    "Some of the selected Delivery order is not in transit state"))
        return records.button_validate()
