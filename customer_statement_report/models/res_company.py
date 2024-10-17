from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    last_statement_date = fields.Date(string="Last Email Statement Date")
    last_pdf_statement_date = fields.Date(string="Last PDF Statement Date")
