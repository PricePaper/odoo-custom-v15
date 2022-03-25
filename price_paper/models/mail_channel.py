from odoo import _, api, fields, models


class Channel(models.Model):

    _inherit = 'mail.channel'

    def _inverse_channel_partner_ids(self):
        new_members = []
        outdated = self.env['mail.channel.partner']
        for channel in self:
            current_members = channel.channel_last_seen_partner_ids
            partners = channel.channel_partner_ids
            partners_new = partners - current_members.partner_id

            new_members += [{
                'channel_id': channel.id,
                'partner_id': partner.id,
            } for partner in partners_new]
            outdated += current_members.filtered(lambda m: m.partner_id not in partners)

        if new_members:
            self.env['mail.channel.partner'].create(new_members)
        if outdated:
            outdated.sudo().unlink()
