# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ProductCategory(models.Model):
    _inherit = 'product.category'

    is_storage_contract = fields.Boolean(string='Is storage contract')
    sc_stock_valuation_account_id = fields.Many2one(
        'account.account',
        string="SC Stock Valuation Account"
    )
    sc_stock_liability_account_id = fields.Many2one(
        'account.account',
        string="SC stock liability account"
    )

    repacking_upcharge = fields.Float(string="Repacking Charge %")
    categ_code = fields.Char(string='Category Code')
    standard_price = fields.Float(
        string="Class Standard Price Percent",
        digits='Product Price')

    inv_adj_output_account_id = fields.Many2one(
        'account.account',
        company_dependent=True,
        string="Inventory Adjustment Output Account",
        domain=[('deprecated', '=', False)]
    )
    inv_adj_input_account_id = fields.Many2one(
        'account.account',
        company_dependent=True,
        string="Inventory Adjustment Input Account",
        domain=[('deprecated', '=', False)]
    )
