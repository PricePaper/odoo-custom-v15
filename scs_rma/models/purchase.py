# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    rma_done = fields.Boolean("RMA is Done", copy=False)
