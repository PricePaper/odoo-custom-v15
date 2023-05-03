# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, models, fields, _
from odoo.http import request
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit='sale.order'

    is_sample_order = fields.Boolean(string='Sample Order',default=False)

    @api.model
    def create(self, vals):
        if vals.get('is_sample_order'):
            sequence = self.env.ref('sample_request.seq_sc_sale_order_sample', raise_if_not_found=False)
            if sequence:
                vals['name'] = sequence._next()
        order = super(SaleOrder, self).create(vals)
        return order



    def action_confirm(self):
        """
        create record in price history
        and also update the customer pricelist if needed.
        create invoice for bill_with_goods customers.

        """
        if self.is_sample_order:
            self = self.with_context(from_import=True)
        return super(SaleOrder, self).action_confirm()

        
class SampleRequest(models.Model):
    _name = "sample.request"
    _descriptin='Model for requesting the samples'
    _inherit = ['mail.thread']

    name = fields.Char(string='Name')
    partner_id = fields.Many2one('res.partner',string='Customer')
    partner_shipping_id = fields.Many2one('res.partner')
    request_lines = fields.One2many('sample.request.line','request_id',string='Sample Requests')
    state = fields.Selection([('draft','Draft'),('request','Request'),('reject','Rejected'),('approve','Approved')],default='draft',tracking=True)
    sale_id = fields.Many2one('sale.order',string='Order')
    carrier_id = fields.Many2one('delivery.carrier',string='Delivery Method')



    
    def approve_request(self):
        if not self.carrier_id:
            raise UserError('Select the delivery method before approval')
        route = self.env['ir.config_parameter'].sudo().get_param('sample_request.sample_route')
        route = int(route) if route else False
        sale_id = self.env['sale.order'].sudo().create({
            'partner_id':self.partner_id.id,
            'invoice_address_id':self.partner_id.id,
            'is_sample_order':True,
            'carrier_id':self.carrier_id.id,
            'partner_shipping_id':self.partner_shipping_id.id if self.partner_shipping_id else self.partner_id.id,
            'order_line':[(0,0,{'product_id':res.product_id.id,'discount':100,'route_id':route}) for res in self.request_lines]
        })
        self.sale_id = sale_id
        self.state='approve'
        return True


    def sent_approval(self):
        self.state='request'


    def reject_request(self):

        """To Reject Request"""
        return {
            'name': ("Reject Reason"),
                'view_mode': 'form',
                'view_id': False,
                'res_model': 'reject.reason',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
        }
        # self.state = 'reject'



        

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            vals['name'] = self.env['ir.sequence'].next_by_code('sample.request', sequence_date=seq_date) or _('New')
        result = super(SampleRequest, self).create(vals)
        return result

    def _update_sample_order(self,product_id):
        """ TO Update the sample order on the basis of rules"""
        allow_sample = self.env['ir.config_parameter'].sudo().get_param('sample_request.allow_sample')
        if not allow_sample:
            return {'error':'Sample requests have been  blocked.'}
        
        limit = self.env['ir.config_parameter'].sudo().get_param('sample_request.max_sample')
        months = self.env['ir.config_parameter'].sudo().get_param('sample_request.request_months') or  0
        requests = self.search_count([('partner_id','=',self.partner_id.id),('state','=','approve'),('create_date','>=',str(datetime.now() - relativedelta(months=int(months))))])
        if requests >= int(limit):
            return {'error':'You have reached the sample request limit.'}
        
        allow_repeat = self.env['ir.config_parameter'].sudo().get_param('sample_request.allow_repeat')

        if not allow_repeat:
            sample_requests = self.search([('partner_id','=',self.partner_id.id),('state','=','approve')]).request_lines.filtered(lambda line:line.product_id.id==int(product_id))
            if sample_requests:
                return {'error':'You have already requested sample for this product, repeat orders are not allowed.'}
             

        sample_requests = self.request_lines.filtered(lambda line:line.product_id.id==int(product_id))
        if not sample_requests:
            self.request_lines=[(0,0,{'product_id':int(product_id)})]
        return {}


class SampleRequestLine(models.Model):
    _name = "sample.request.line"

    request_id = fields.Many2one('sample.request')
    product_id = fields.Many2one('product.product','Product')
