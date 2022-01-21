# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class Lead(models.Model):
    _inherit = "crm.lead"

    rev_per_trans = fields.Float(string="Revenue Per Transaction")
    business_freq = fields.Selection(selection=[('week', 'Weekly'),
                                                ('biweek', 'Biweekly'),
                                                ('month', 'Monthly')], string="Frequency")
#    planned_revenue = fields.Float(compute="_calc_expected_revenue", string='Monthly Revenue Expected', store=True)#Planned_revenue changed to expected revenue v15
    expected_revenue = fields.Float(compute="_calc_expected_revenue", string='Monthly Revenue Expected', store=True)
    sales_person_ids = fields.Many2many('res.partner', string="Sales Persons")

    @api.depends('rev_per_trans', 'business_freq')
    def _calc_expected_revenue(self):
        """
        calculates the expected revenue
        multiplies frequency and revenue
        per transaction
        """
        for lead in self:
            if lead.rev_per_trans and lead.business_freq:
                if lead.business_freq == 'week':
                    lead.expected_revenue = lead.rev_per_trans * 4
                elif lead.business_freq == 'biweek':
                    lead.expected_revenue = lead.rev_per_trans * 2
                elif lead.business_freq == 'month':
                    lead.expected_revenue = lead.rev_per_trans

    def write(self, vals):
        """
        if the lead has got business_freq
        and revenue/transaction info associated with them,
        then copy it down to the partner when the lead is
        associated with one
        """
        res = super(Lead, self).write(vals)
        for lead in self:
            if lead.partner_id and (vals.get('rev_per_trans', False) or vals.get('business_freq', '')): #note: check this condition is as per the requirement
                partner = lead.partner_id
                partner.rev_per_trans = lead.rev_per_trans or vals.get('rev_per_trans', 0.00)
                partner.business_freq = lead.business_freq or vals.get('business_freq', '')


    def _prepare_customer_values(self, partner_name, is_company=False, parent_id=False):
        """Adding sales persons data while creating partner from Convert to opportunity wizard 
        with Create a new customer option"""

        result = super(Lead, self)._prepare_customer_values(partner_name,is_company,parent_id)
        result['sales_person_ids'] = [(6, 0, self.sales_person_ids.ids)]
        return result

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        return super(Lead, self.with_context(mail_post_autofollow=False)).message_post(**kwargs)



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
