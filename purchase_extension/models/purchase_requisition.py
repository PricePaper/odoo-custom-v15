# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    supplier_ids = fields.Many2many('res.partner', string="Suppliers")



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
