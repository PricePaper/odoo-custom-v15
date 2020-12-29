# -*- coding: utf-8 -*-

from odoo import fields, models


class ZipDeliveryDay(models.Model):
    _name = 'zip.delivery.day'
    _rec_name = 'zip'

    zip = fields.Char(string='Zip')
    delivery_day_mon = fields.Boolean(string='Monday')
    delivery_day_tue = fields.Boolean(string='Tuesday')
    delivery_day_wed = fields.Boolean(string='Wednesday')
    delivery_day_thu = fields.Boolean(string='Thursday')
    delivery_day_fri = fields.Boolean(string='Friday')
    delivery_day_sat = fields.Boolean(string='Saturday')
    delivery_day_sun = fields.Boolean(string='Sunday')
    shipping_easiness = fields.Selection([('easy', 'Easy'), ('neutral', 'Neutral'), ('hard', 'Hard')],
                                         string='Easiness of shipping')

    _sql_constraints = [('zip', 'unique(zip)', 'Choose another zip value - Record already exists!')]


ZipDeliveryDay()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
