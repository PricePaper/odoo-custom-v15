from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero



class StockPicking(models.Model):
    _inherit = 'stock.picking'


    def validate_multiple_delivery(self):
        for rec in self:
            if rec.state not in ('in_transit', 'transit_confirmed') and not rec.rma_id and not rec.purchase_id:
                raise UserError(_(
                    "Some of the selected Delivery order is not in transit state"))
            rec.button_validate()
        return {'type': 'ir.actions.act_window_close'}

    def _action_done(self):
        if self.rma_id:
            res = super(StockPicking, self)._action_done()

            invoice_ids = self.move_lines.mapped('invoice_line_ids').mapped('move_id')

            if invoice_ids:
                return res

            #create invoice
            rma = self.rma_id
            invoice_line_vals = []
            for rma_line in rma.rma_sale_lines_ids:
                move_line = self.move_lines.filtered(lambda r: r.state == 'done' and r.product_id == rma_line.product_id)
                if not move_line:
                    continue

                inv_account_id = rma_line.product_id. \
                                     property_account_income_id and \
                                 rma_line.product_id. \
                                     property_account_income_id.id or \
                                 rma_line.product_id.categ_id. \
                                     property_account_income_categ_id and \
                                 rma_line.product_id.categ_id. \
                                     property_account_income_categ_id.id or False
                if not inv_account_id:
                    raise ValidationError((
                                              'No account defined for product "%s".') %
                                          rma_line.product_id.name)
                prod_price = 0.0
                if rma_line.refund_qty != 0:
                    prod_price = float(
                        (rma_line.refund_price) / float(
                            rma_line.refund_qty))
                inv_line_values = {
                    'product_id': rma_line.product_id and rma_line.
                        product_id.id or False,
                    'account_id': inv_account_id or False,
                    'name': rma_line.product_id and rma_line.
                        product_id.name or False,
                    'quantity': move_line.quantity_done or 0,
                    'product_uom_id': rma_line.return_product_uom and rma_line.return_product_uom.id or False,
                    'price_unit': prod_price or 0,
                    'currency_id': rma.currency_id.id or False,
                    'stock_move_id': move_line.id,
                    'sale_line_ids': [(6, 0, [rma_line.so_line_id.id])]
                }

                if rma_line.tax_id and rma_line.tax_id.ids:
                    inv_line_values.update(
                        {'tax_ids': [(6, 0, rma_line.
                                                   tax_id.ids)]})

                invoice_line_vals.append((0, 0, inv_line_values))
            if invoice_line_vals:
                inv_values = {
                    'move_type': 'out_refund',
                    'invoice_origin': rma.name or '',
                    #'comment': rma.problem or '',
                    'partner_id': rma.invoice_address_id and
                                  rma.invoice_address_id.id or False,
                    #'account_id':
                      #  rma.invoice_address_id.property_account_receivable_id and
                       # rma.invoice_address_id.property_account_receivable_id.id or
                       # False,
                    'invoice_line_ids': invoice_line_vals,
                    'invoice_date': rma.rma_date or False,
                    'rma_id': rma.id,
                }
                salereps = rma.mapped('rma_sale_lines_ids').mapped('so_line_id').mapped('order_id').mapped('sales_person_ids')
                commission_rule_ids = rma.mapped('rma_sale_lines_ids').mapped('so_line_id').mapped('order_id').mapped('commission_rule_ids')
                if salereps:
                    inv_values['sales_person_ids'] = [(6, 0, salereps.ids)]
                if commission_rule_ids:
                    inv_values['commission_rule_ids'] = [(6, 0, commission_rule_ids.ids)]
                inv = self.env['account.move'].with_context(mail_create_nosubscribe=True).create(inv_values)
                # for inv_line in inv.invoice_line_ids:
                #     for move_line in self.move_lines.filtered(lambda r: r.state == 'done'):
                #         if inv_line.product_id == move_line.product_id and inv_line.quantity == move_line.product_uom_qty:
                #             inv_line.write({'stock_move_id': move_line.id, 'quantity': move_line.quantity_done})
                #             break
            return res
        else:
            return super(StockPicking, self)._action_done()


class StockMove(models.Model):
    _inherit = 'stock.move'


    def _get_price_unit(self):
        """ Override to return RMA moves's price"""
        self.ensure_one()
        if self.picking_id and self.picking_id.rma_id:
            original_move = self.sale_line_id.move_ids.filtered(lambda r: r.picking_code == 'outgoing')
            if original_move:
                layers = original_move.sudo().stock_valuation_layer_ids
                if layers:
                    quantity = sum(layers.mapped("quantity"))
                    if not float_is_zero(quantity, precision_rounding=layers.uom_id.rounding):
                        return  layers.currency_id.round(sum(layers.mapped("value")) / quantity)
        return super(StockMove, self)._get_price_unit()
