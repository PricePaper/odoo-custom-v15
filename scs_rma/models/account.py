# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    rma_id = fields.Many2one('rma.ret.mer.auth', string='RMA')
