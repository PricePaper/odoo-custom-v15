from odoo import models, fields, api, _


class AccountJournal(models.Model):
    _inherit = 'account.journal'


    private_journal = fields.Boolean(string='Is Private Journal', default=False)


