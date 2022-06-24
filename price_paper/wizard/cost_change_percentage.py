# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CostChangePercentage(models.TransientModel):
    _name = 'cost.change.percentage'
    _description = "Cost change percentage"

    percentage_change = fields.Float(string='Percentage change')

    def add_cost_change_lines(self):
        """
        Creating cost change lines
        """

        self.ensure_one()
        active_id = self._context.get('active_id')
        cost_change_parent = self.env['cost.change.parent'].browse(active_id)
        product_ids = self.env['product.product']
        for rec in cost_change_parent:
            domain = []
            if rec.vendor_id:
                product_ids = self.env['product.supplierinfo'].search(
                    [('name', '=', rec.vendor_id.id), ('product_id', '!=', False)]).mapped('product_id')
                domain.append(('id', 'in', product_ids.ids))
            if rec.category_id:
                domain.append(('categ_id.id', 'child_of', rec.category_id.ids))
            products = self.env['product.product'].search(domain)
            if products:
                product_ids = products
        for product in product_ids:
            vendor_res = product.seller_ids.filtered(lambda r: r.name == cost_change_parent.vendor_id)
            product_code = vendor_res.mapped('product_code')
            v_code = ''
            for code in product_code:
                if code != False:
                    v_code = code
                    break
            vend_seq = vendor_res.mapped('sequence')
            non_seq = product.seller_ids.filtered(lambda r: r.name != cost_change_parent.vendor_id and (
                    not r.date_end or r.date_end > fields.Date.today())).mapped('sequence')
            if not non_seq or min(vend_seq) <= min(non_seq):
                cost_change_line = {
                    'vendor_product_code': v_code,
                    'product_id': product.id,
                    'price_filter': 'percentage',
                    'price_change': self.percentage_change,
                    'burden_change': product.burden_percent,
                    'cost_change_parent': cost_change_parent and cost_change_parent.id
                }
                if self.percentage_change == 0:
                    cost_change_line.update({'price_filter': 'fixed',
                                             'price_change': product.standard_price})
                self.env['cost.change'].create(cost_change_line)
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
