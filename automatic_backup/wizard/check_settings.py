from odoo import models, fields, api

class Check_Settings(models.TransientModel):
    _name = 'check.settings'
    _description = "Settings are correct"

    yes_no = fields.Char(default='Settings are correct!!')