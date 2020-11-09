from odoo import api, fields, models, _


class Accountinvoice(models.Model):
    _inherit = "account.invoice"

    def remove_sale_commission(self):
        return True


Accountinvoice()
