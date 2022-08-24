# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round

class StockValuationPriceDiff(models.TransientModel):
    _name = 'stock.valuation.price.diff.wizard'
    _description = 'Stock valuation price Diff Wizard'

    def generate_report(self):
        records = self.env['stock.valuation.layer'].search([('remaining_qty', '>', 0)])
        for rec in records:
            if rec.stock_move_id and rec.stock_move_id.picking_id and rec.stock_move_id.picking_id.rma_id:
                continue
            price_diff = False
            svl_recs = rec.product_id.stock_valuation_layer_ids.filtered(lambda r: r.remaining_qty != 0 and r.create_date > rec.create_date)
            is_greater = True
            for svl_rec in svl_recs:
                if svl_rec.stock_move_id and svl_rec.stock_move_id.picking_id and svl_rec.stock_move_id.picking_id.rma_id:
                    continue
                is_greater = False
                break
            if is_greater:
                if float_round(rec.product_id.standard_price, 2) != float_round(rec.unit_cost, 2):
                    price_diff = True
                elif rec.product_id.seller_ids and float_round(rec.product_id.seller_ids[0].price, 2) != float_round(rec.unit_cost, 2):
                    price_diff = True
            if price_diff:
                seller = rec.product_id.seller_ids
                seller_id = False
                seller_price = 0
                if seller:
                    seller_id = seller[0].name.id
                    seller_price = seller[0].price
                new_vals = {
                            'company_id': rec.company_id.id,
                            'move_date': rec.create_date,
                            'product_id': rec.product_id.id,
                            'categ_id': rec.product_id.categ_id.id,
                            'quantity':rec.quantity,
                            'uom_id':rec.uom_id.id,
                            'currency_id': rec.company_id.currency_id.id,
                            'unit_cost': rec.unit_cost,
                            'value': rec.value,
                            'remaining_qty': rec.remaining_qty,
                            'remaining_value': rec.remaining_value,
                            'stock_move_id': rec.stock_move_id.id,
                            'account_move_id': rec.account_move_id.id,
                            'product_price': rec.product_id.standard_price,
                            'seller_id': seller_id,
                            'seller_price': seller_price,
                            'wizard_id': self.id
                            }
                self.env['stock.valuation.price.diff'].create(new_vals)
        action = self.sudo().env.ref('batch_delivery.stock_valuation_layer_price_diff_action').read()[0]
        if action:
            action.update({
                'domain': [["wizard_id", "=", self.id]],
            })
            return action


class StockValuationPriceDiff(models.TransientModel):
    _name = 'stock.valuation.price.diff'
    _description = 'Stock valuation price Diff'

    _order = 'move_date, id'

    _rec_name = 'product_id'

    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True,)
    categ_id = fields.Many2one('product.category', 'Product Category',readonly=True)
    quantity = fields.Float('Quantity', help='Quantity', readonly=True, digits='Product Unit of Measure')
    uom_id = fields.Many2one('uom.uom', 'UOM', readonly=True, required=True)
    currency_id = fields.Many2one('res.currency', 'Currency', readonly=True)
    unit_cost = fields.Monetary('FIFO Cost', readonly=True)
    value = fields.Monetary('Total Value', readonly=True)
    remaining_qty = fields.Float(readonly=True, digits='Product Unit of Measure')
    remaining_value = fields.Monetary('Remaining Value', readonly=True)
    description = fields.Char('Description', readonly=True)
    stock_move_id = fields.Many2one('stock.move', 'Stock Move', readonly=True, check_company=True, index=True)
    account_move_id = fields.Many2one('account.move', 'Journal Entry', readonly=True, check_company=True)
    product_price = fields.Float(string='Product Cost', digits='Product Price', readonly=True)
    seller_price = fields.Float(string='Vendor Price', digits='Product Price', readonly=True)
    seller_id = fields.Many2one('res.partner', string='Vendor', readonly=True)
    move_date = fields.Datetime('Date', readonly=True)
    wizard_id = fields.Many2one('stock.valuation.price.diff.wizard', string='Wizard')
