# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class CostChangeParent(models.Model):
    _inherit = 'cost.change.parent'

    landed_cost_id = fields.Many2one('stock.landed.cost', 'Landed Cost', copy=False)
