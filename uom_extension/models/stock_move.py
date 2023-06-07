# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.float_utils import float_round


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):

        if self._context.get('check_uom_change', None):
            args += [('state', 'not in', ['done', 'cancel'])]
        return super(StockMove, self).search(args, offset, limit, order, count=count)

    def wrapper_action_done_inventory(self):
        self._action_done()
        return True
