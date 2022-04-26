# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.onchange('product_id', 'company_id')
    def _onchange_product_id(self):
        product_id = self.product_id
        location_src = product_id and product_id.property_stock_location and \
                       product_id.property_stock_location.id or product_id and \
                       product_id.categ_id and product_id.categ_id.property_stock_location and \
                       product_id.categ_id.property_stock_location.id or False
        if self.product_id.tracking in ['lot', 'serial']:
            previous_quants = self.env['stock.quant'].search([
                ('product_id', '=', self.product_id.id),
                ('location_id.usage', 'in', ['internal', 'transit'])], limit=1, order='create_date desc')
            if previous_quants:
                self.location_id = previous_quants.location_id
        else:
            company_id = self.company_id and self.company_id.id or self.env.company.id
            if location_src and not product_id.qty_available:
                self.location_id = location_src
            else:
                self.location_id = self.env['stock.warehouse'].search(
                    [('company_id', '=', company_id)], limit=1).in_type_id.default_location_dest_id

    @api.model
    def _update_reserved_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None, strict=False):
        """ Increase the reserved quantity, i.e. increase `reserved_quantity` for the set of quants
        sharing the combination of `product_id, location_id` if `strict` is set to False or sharing
        the *exact same characteristics* otherwise. Typically, this method is called when reserving
        a move or updating a reserved move line. When reserving a chained move, the strict flag
        should be enabled (to reserve exactly what was brought). When the move is MTS,it could take
        anything from the stock, so we disable the flag. When editing a move line, we naturally
        enable the flag, to reflect the reservation according to the edition.

        :return: a list of tuples (quant, quantity_reserved) showing on which quant the reservation
            was done and how much the system was able to reserve on it
        """
        self = self.sudo()
        rounding = product_id.uom_id.rounding
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict)
        rounding_digit = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        quantity = float_round(quantity, precision_digits=rounding_digit)
        if float_compare(quantity, 0, precision_rounding=rounding) > 0:
            # if we want to reserve
            available_quantity = self._get_available_quantity(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id,
                                                              strict=strict)
            available_quantity = float_round(available_quantity, precision_digits=rounding_digit)
            if float_compare(quantity, available_quantity, precision_rounding=rounding) > 0:
                raise UserError(_('It is not possible to reserve more products of %s than you have in stock.', product_id.display_name))
        elif float_compare(quantity, 0, precision_rounding=rounding) < 0:
            # if we want to unreserve
            available_quantity = sum(quants.mapped('reserved_quantity'))
            available_quantity = float_round(available_quantity, precision_digits=rounding_digit)
            if float_compare(abs(quantity), available_quantity, precision_rounding=rounding) > 0:
                raise UserError(_('It is not possible to unreserve %s  products of %s \n  you have %s in %s.',
                                  abs(quantity), product_id.display_name, available_quantity, location_id.display_name))
        return super()._update_reserved_quantity(product_id, location_id, quantity, lot_id, package_id, owner_id, strict)
