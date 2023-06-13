# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    vendor_bill_ids = fields.Many2many(comodel_name='account.move', relation='account_move_stock_landed_cost_rel',
                                       column1='landed_cost_id', column2='vendor_bill_id')

    def button_validate(self):
        res = super().button_validate()
        for cost in self:
            if cost.vendor_bill_ids:
                for bill in cost.vendor_bill_ids:
                    if bill.state == 'posted' and cost.company_id.anglo_saxon_accounting:
                        all_amls = bill.line_ids | cost.account_move_id.line_ids
                        for product in cost.cost_lines.product_id:
                            accounts = product.product_tmpl_id.get_product_accounts()
                            input_account = accounts['stock_input']
                            all_amls.filtered(lambda aml: aml.account_id == input_account and not aml.reconciled).reconcile()
        return res


class StockLandedCostLine(models.Model):
    _inherit = 'stock.landed.cost.lines'

    move_line_id = fields.Many2one('account.move.line', 'Invoice Line')
    move_id = fields.Many2one('account.move', 'Invoice', related="move_line_id.move_id")
