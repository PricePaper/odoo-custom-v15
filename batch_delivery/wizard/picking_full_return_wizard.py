# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PickingFullReturnWizard(models.TransientModel):
    _name = 'picking.full.return.wizard'
    _description = 'Picking full return'

    picking_id = fields.Many2one('stock.picking', string='Picking',
                                 default=lambda self: self.env['stock.picking'].browse(self._context.get('active_id')))
    sale_id = fields.Many2one(related='picking_id.sale_id', readonly=True)

    def create_full_return(self):
        # pass
        picking = self.picking_id
        sale = self.sale_id
        picking.check_return_reason()
        self.env['stock.picking.return'].create({
            'name': 'RETURN-' + picking.name,
            'picking_id': picking.id,
            'sale_id': sale.id,
            'sales_person_ids': [(6, 0, sale.sales_person_ids and sale.sales_person_ids.ids)],
            'return_line_ids': [(0, 0, {
                'product_id': move.product_id.id,
                'ordered_qty': move.product_uom_qty,
                'delivered_qty': 0,
                'reason_id': move.reason_id.id
            }) for move in picking.move_lines]
        })
        picking.write({'is_transit': False, 'batch_id': False, 'is_transit_confirmed': False})
        # picking.mapped('move_line_ids').write({'qty_done': 0})

        for move in picking.move_lines:
            move.sale_line_id.qty_delivered -= move.quantity_done
        picking.mapped('move_lines').write({'quantity_done': 0})
        # order = self.env['sale.order.line'].search([('order_id', '=', picking.sale_id.id), ('is_delivery', '=', True)])
        delivery_line = sale.mapped('order_line').filtered(lambda rec: rec.is_delivery is True)
        delivery_line.write({'product_uom_qty': delivery_line.product_uom_qty + 1})
        invoice = sale.invoice_ids.filtered(lambda rec: picking in rec.picking_ids)
        invoice.button_cancel()
        return True


PickingFullReturnWizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
