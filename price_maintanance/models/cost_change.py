# -*- coding: utf-8 -*-

from odoo import models, api


class CostChange(models.Model):
    _inherit = 'cost.change'

    @api.model
    def default_get(self, fields_list):
        res = super(CostChange, self).default_get(fields_list)
        if self._context.get('product_id', False):
            res['product_id'] = self._context.get('product_id')
        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
