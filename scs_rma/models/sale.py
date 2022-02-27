# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    rma_done = fields.Boolean("RMA is Done", copy=False)
