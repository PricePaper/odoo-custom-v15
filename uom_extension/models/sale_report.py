# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleReport(models.Model):
    _inherit = 'sale.report'

    def _select_sale(self, fields=None):
        if not fields:
            fields = {}
        select_ = super(SaleReport, self)._select_sale(fields)
        select_ = select_.replace('t.uom_id', 't.ppt_uom_id')
        x = 'CASE WHEN l.product_id IS NOT NULL THEN sum(l.product_uom_qty / u.factor * u2.factor) ELSE 0 END as product_uom_qty,'
        y = 'CASE WHEN l.product_id IS NOT NULL AND superseed.product_child_id IS NOT NULL THEN sum(l.product_uom_qty / u.factor * new_u.factor) WHEN l.product_id IS NOT NULL THEN sum(l.product_uom_qty / u.factor * u2.factor) ELSE 0 END as product_uom_qty,'
        select_ = select_.replace(x, y)
        return select_

    def _from_sale(self, from_clause=''):
        from_ = super(SaleReport, self)._from_sale()
        from_ = from_.replace("uom_id", 'ppt_uom_id')
        x = "left join product_pricelist pp on (s.pricelist_id = pp.id)"
        y = "left join product_pricelist pp on (s.pricelist_id = pp.id) left join product_superseded as superseed on (superseed.old_product = l.product_id) left join product_product new_p on (superseed.product_child_id=new_p.id) left join product_template new_t on (new_p.product_tmpl_id=new_t.id) left join uom_uom new_u on (new_u.id=new_t.ppt_uom_id)"
        from_ = from_.replace(x, y)
        return from_

    def _group_by_sale(self, groupby=''):
        groupby_ = super()._group_by_sale(groupby)
        # groupby_ = groupby_.replace('t.uom_id', 't.ppt_uom_id')
        groupby_ = groupby_.replace('t.uom_id', 't.ppt_uom_id, superseed.product_child_id')
        return groupby_
