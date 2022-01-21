# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools import float_compare


class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    is_available = fields.Boolean(string='Is Available', compute='_compute_supplierinfo_avl', store=True)

    @api.depends('date_start', 'date_end')
    def _compute_supplierinfo_avl(self):
        date = fields.Date.context_today(self)
        for seller in self:
            if seller.date_start and seller.date_start > date:
                seller.is_available = False
            elif seller.date_end and seller.date_end < date:
                seller.is_available = False
            else:
                seller.is_available = True




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
