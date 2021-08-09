# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    default_code = fields.Char(string='Internal Reference', related='product_id.default_code')

    @api.multi
    def write(self, vals):
        """
        overriden to log price change
        """

        for line in self:
            if 'price' in vals:
                log_vals = {'change_date': fields.Datetime.now(),
                            'type': 'vendor_price',
                            'old_price': line.price,
                            'new_price': vals.get('price'),
                            'user_id': self.env.user.id,
                            'uom_id': line.product_uom.id,
                            'price_from': 'manual',
                            'product_id': line.product_id.id,
                            'min_qty': line.min_qty,
                            'partner_ids': [(6, 0, [line.name.id])],
                            }
                if self._context.get('user', False):
                    log_vals['user_id'] = self._context.get('user', False)
                if self._context.get('cost_cron', False):
                    log_vals['price_from'] = 'cost_cron'
                if self._context.get('from_purchase', False):
                    log_vals['price_from'] = 'purchase'
                self.env['product.price.log'].create(log_vals)

        result = super(SupplierInfo, self).write(vals)
        return result

    @api.model
    def create(self, vals):
        """
        overriden to log price change
        """

        res = super(SupplierInfo, self).create(vals)
        log_vals = {
            'change_date': fields.Datetime.now(),
            'type': 'vendor_price',
            'new_price': res.price,
            'user_id': self.env.user.id,
            'uom_id': res.product_uom.id,
            'price_from': 'manual',
            'product_id': res.product_id.id,
            'min_qty': res.min_qty,
            'partner_ids': [(6, 0, [res.name.id])],
        }
        if self._context.get('user', False):
            log_vals['user_id'] = self._context.get('user', False)
        if self._context.get('cost_cron', False):
            log_vals['price_from'] = 'cost_cron'
        if self._context.get('from_purchase', False):
            log_vals['price_from'] = 'purchase'
        self.env['product.price.log'].create(log_vals)
        return res


    @api.model
    def default_get(self, fields_list):
        result = super(SupplierInfo, self).default_get(fields_list)
        result['date_start'] = self.env['ir.config_parameter'].sudo().get_param('purchase_extension.supplier_start_date')
        result['date_end'] = self.env['ir.config_parameter'].sudo().get_param('purchase_extension.supplier_end_date')
        return result


SupplierInfo()

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    supplier_start_date = fields.Char(string='Supplier Start Date', config_parameter='purchase_extension.supplier_start_date')
    supplier_end_date = fields.Char(string='Supplier End Date', config_parameter='purchase_extension.supplier_end_date')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
