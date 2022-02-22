# -*- coding: utf-8 -*-

from odoo import fields, models, api


class PriceEditNotes(models.Model):
    _name = 'price.edit.notes'
    _description = 'Price Edit Notes'
    _order = "edit_date desc"

    product_id = fields.Many2one('product.product', string='Product')
    partner_id = fields.Many2one('res.partner', string='Customer')
    note = fields.Text(string='Notes')
    edit_date = fields.Datetime(string='Date')
    user_id = fields.Many2one('res.users', string="Edited by")

    @api.depends('product_id', 'edit_date')
    def name_get(self):
        result = []
        for record in self:
            name = "%s_%s" % (
            record.product_id and record.product_id.name or '', record.edit_date and record.edit_date or '')
            result.append((record.id, name))
        return result



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
