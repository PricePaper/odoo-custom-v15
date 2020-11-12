# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_pricelist_line_ids = fields.Many2many('customer.product.price', store=False, string="Customer Pricelist line", compute="_compute_pricelist_lines")
    change_flag = fields.Boolean(string='Log an Audit Note')
    audit_notes = fields.Text(string='Audit Note')
    partner_pricelist_id = fields.Many2one('customer.pricelist', string="Pricelist", store=False, compute='_compute_pricelist')


    def _compute_pricelist(self):
        for partner in self:
            pricelist = False
            if partner.customer_pricelist_ids:
                pricelist = partner.customer_pricelist_ids.filtered(lambda r: r.sequence == 0)
                if pricelist:
                    pricelist =  pricelist.id
                else:
                    pricelist = partner.customer_pricelist_ids[0].id
            partner.partner_pricelist_id = pricelist


    @api.depends('partner_pricelist_id')
    def _compute_pricelist_lines(self):
        for partner in self:
            if partner.partner_pricelist_id:
                price_list_lines = partner.partner_pricelist_id.pricelist_id.customer_product_price_ids.ids
                if price_list_lines:
                    partner.partner_pricelist_line_ids = [(6, 0, price_list_lines)]
            else:
                partner.partner_pricelist_line_ids = False



#    @api.multi
#    @api.onchange('customer_pricelist_line_ids.price')
#    def onchange_change_flag(self):
#        action = self.env.ref('price_maintanance.action_price_maintanace')
#        action = action and action.id
#        context_action = self._context.get('params', {}).get('action', False)

#        if context_action == action:
#            if not self.change_flag:
#                self.change_flag = True
#                res =  {'warning': {
#                                    'title': _('Warning'),
#                                    'message': _('You have made changes in this form. Please do not forget to enter an audit note under the bottom part of the screen before you save.')
#                                   }
#                       }
#                return res




    @api.multi
    def create_audit_notes(self, audit_notes):
        for partner in self:
            partner.env['price.edit.notes'].create({
                                                    'partner_id': partner.id,
                                                    'edit_date': fields.Datetime.now(),
                                                    'note': audit_notes,
                                                    'user_id': self.env.user.id
                                                   })


    @api.multi
    def write(self, vals):
        change_flag = vals.pop('change_flag', False)
        audit_notes = vals.pop('audit_notes', False)
        if vals.get('customer_pricelist_line_ids', False) and not change_flag:
            raise ValidationError(_('You have made changes in this form. Please enter an audit note under the bottom part of the screen before you save.'))
        elif change_flag:
            self.create_audit_notes(audit_notes)
        res = super(ResPartner, self).write(vals)
        return res






ResPartner()
