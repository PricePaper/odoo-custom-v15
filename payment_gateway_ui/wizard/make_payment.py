# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError


class make_payment(models.TransientModel):
    _name = "make.payment"
    _description = "Make Payment Class"


    @api.model
    def _get_partner_id(self):
        partner_brw = self.env['res.partner'].browse(self._context.get('default_partner_id', False))
        return partner_brw.id


    def gateway_transaction(self):
        self.ensure_one()




        return True
 
    card_no = fields.Char('Credit Card Number', size=16)
    card_code = fields.Char('CVV', size=4)
    exp_month = fields.Selection(
        [('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'), ('05', 'May'), ('06', 'June'),
         ('07', 'July'), ('08', 'August'), ('09', 'September'), ('10', 'October'), ('11', 'November'),
         ('12', 'December')], 'Card Expiration Month')
    exp_year = fields.Selection([(str(num), str(num)) for num in range(datetime.now().year, (datetime.now().year) + 11)],
                                'Card Expiration Year')
    partner_id = fields.Many2one('res.partner', "Partner Invoice Address", default=_get_partner_id)
    is_correction = fields.Boolean('Is Correction')
    gateway_type = fields.Selection([], string='Payment Gateway')




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
