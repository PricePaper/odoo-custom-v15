# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AddPortalContacts(models.TransientModel):

    _name = "add.portal.contacts"

    portal_wizard_contact_ids = fields.Many2many('res.partner', string="Contacts")
    company_id = fields.Many2one('res.partner', string="Company", readonly=True)

    def action_add_contacts_to_portal_user(self):
        origin_id = self._context.get('origin_id', None)
        origin_model = self._context.get('origin_model')

        if origin_model == 'res.partner' and origin_id:

            portal_partner = self.env['res.partner'].browse([origin_id])
            portal_contacts = portal_partner.portal_contact_ids.filtered(lambda x: (x.partner_id.id == self.company_id.id and not x.parent_id) or x.parent_id.id == self.company_id.id)
            removed_contact_ids = portal_contacts.mapped('partner_id') - self.company_id
            portal_contacts.unlink()

            if not self.portal_wizard_contact_ids:
                portal_partner.write({'portal_contact_ids': [(0, 0, {'partner_id': self.company_id.id})]})

            else:
                contacts_values = [
                    (0, 0, {'partner_id': contact.id,
                            'parent_id': self.company_id.id})
                    for contact in self.portal_wizard_contact_ids
                ]

                portal_partner.write({'portal_contact_ids': contacts_values})

            added_contact_ids = self.portal_wizard_contact_ids - removed_contact_ids
            removed_contact_ids = removed_contact_ids - self.portal_wizard_contact_ids

            if added_contact_ids:
                added_contact_names = '<li>' + '</li><li>'.join(added_contact_ids.mapped('name')) + '</li>'
                portal_partner.message_post(
                    body=f'Contacts Added:<br/>Related Company: <span style="color: blue;"><b>{self.company_id.name}</b><br/><ul><span style="color: green;">{added_contact_names}</span></ul>')
            if removed_contact_ids:
                removed_contact_names = '<li>' + '</li><li>'.join(removed_contact_ids.mapped('name')) + '</li>'
                portal_partner.message_post(
                    body=f'Contacts Removed:<br/>Related Company: <span style="color: blue;"><b>{self.company_id.name}</b></span><br/><ul><span style="color: red;">{removed_contact_names}</span></ul>')

            portal_partner.clear_caches()
        return {'type': 'ir.actions.act_window_close'}


