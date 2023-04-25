# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    landed_costs_ids2 = fields.Many2many(comodel_name='stock.landed.cost', relation='account_move_stock_landed_cost_rel',
                                         column1='vendor_bill_id', column2='landed_cost_id', string="Vendor")
    # comodel_name = "res.users", relation = "muk_utils_mixins_groups_explicit_users_rel",
    # column1 = "gid", column2 = "uid",
    def action_create_landed_cost(self):
        landed_costs_lines = self.mapped('line_ids').filtered(lambda line: line.is_landed_costs_line)
        landed_costs = self.env['stock.landed.cost'].create({
            'vendor_bill_ids': [(4, rec.id) for rec in self if len(rec.line_ids.filtered(lambda line: line.is_landed_costs_line)) > 0],
            'cost_lines': [(0, 0, {
                'product_id': l.product_id.id,
                'name': l.product_id.name,
                'account_id': l.product_id.product_tmpl_id.get_product_accounts()['stock_input'].id,
                'price_unit': l.currency_id._convert(l.price_subtotal, l.company_currency_id, l.company_id, l.move_id.date),
                'split_method': l.product_id.split_method_landed_cost or 'equal',
            }) for l in landed_costs_lines],
        })
        action = self.env["ir.actions.actions"]._for_xml_id("stock_landed_costs.action_stock_landed_cost")
        return dict(action, view_mode='form', res_id=landed_costs.id, views=[(False, 'form')])

    def action_view_landed_costs(self):
        self.ensure_one()
        if self.landed_costs_ids2:
            action = self.env["ir.actions.actions"]._for_xml_id("stock_landed_costs.action_stock_landed_cost")
            domain = [('id', 'in', self.landed_costs_ids2.ids)]
            context = dict(self.env.context, default_vendor_bill_id=self.id)
            views = [(self.env.ref('stock_landed_costs.view_stock_landed_cost_tree2').id, 'tree'), (False, 'form'), (False, 'kanban')]
            return dict(action, domain=domain, context=context, views=views)
        return super().action_view_landed_costs()