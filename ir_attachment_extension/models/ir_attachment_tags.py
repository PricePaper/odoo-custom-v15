
from odoo import api, fields, models, tools, _


class IrAttachmentTags(models.Model):
    _name = 'ir.attachment.tags'
    _description = 'Attachment tags'

    name = fields.Char(string='Name')
    description = fields.Char(string='Description')
    active = fields.Boolean(string='Is Active?', default='True')

class IrAttachment(models.Model):

    _inherit = 'ir.attachment'

    attachment_tag_id = fields.Many2one('ir.attachment.tags', string='Attachment tag')
