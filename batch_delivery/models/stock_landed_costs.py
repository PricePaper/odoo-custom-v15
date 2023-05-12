# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    cost_cron_ids = fields.One2many('cost.change.parent', 'landed_cost_id', 'Cost Changes')

    def button_create_cost_change(self):
        if self.valuation_adjustment_lines:
            cost_cron = self.env['cost.change.parent'].create({'run_date': False,
                                            'landed_cost_id': self.id})
            product_lines = {}
            for line in self.valuation_adjustment_lines:
                if line.product_id in product_lines:
                    product_lines[line.product_id] += line.additional_landed_cost / line.quantity
                else:
                    product_lines[line.product_id] = line.additional_landed_cost / line.quantity
            for product in product_lines:
                self.env['cost.change'].create(
                    {'price_filter': 'fixed',
                     'product_id': product.id,
                     'price_change': product_lines[product]+product.standard_price,
                     'cost_change_parent': cost_cron.id,
                     })

    def action_view_cost_cron(self):

        cost_cron = self.mapped('cost_cron_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("price_paper.action_cost_change")
        if len(cost_cron) > 1:
            action['domain'] = [('id', 'in', cost_cron.ids)]
        elif len(cost_cron) == 1:
            form_view = [(self.env.ref('price_paper.view_cost_change_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = cost_cron.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


class AdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'

    price_per_unit = fields.Monetary('Cost Per Unit', compute='compute_price_per_unit')

    def compute_price_per_unit(self):
        for line in self:
            line.price_per_unit = line.additional_landed_cost / line.quantity
