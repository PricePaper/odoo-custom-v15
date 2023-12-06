# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import pytz


class SaleHistoryLinesWizard(models.TransientModel):
    _inherit = 'sale.history.lines.wizard'
    _description = 'Sales History Line Wizard'

    main_model = fields.Char(related='search_wizard_id.active_model',store=True)
    add_prod = fields.Boolean(string='Add',default=False)





class AddPurchaseHistorySO(models.TransientModel):
    _inherit = 'add.purchase.history.so'
    _description = "Add Purchase History to SO Line"

    active_model = fields.Char(string='Active Model',default=lambda self:self._context.get('active_model'))
    

    def add_history_lines(self):
        """
        Creating saleorder line with purchase history lines
        """
        if self._context.get('active_model') == 'order.sheet.lines':
            line_ids = self.purchase_history_ids | self.purchase_history_temp_ids
            products = line_ids.filtered(lambda x : x.add_prod).mapped("order_line").mapped('product_id').ids
            if products:
                sheet_id = self.env['order.sheet.lines'].browse([int(self._context['active_id'])])
                vals = [(0,0,{'product_id':product})for product in products]
                # old = sheet_id.product_ids.ids
                # products.extend(old)
                sheet_id.line_product_ids = vals
            
            return True
        else:
            return super(AddPurchaseHistorySO,self).add_history_lines()
        





