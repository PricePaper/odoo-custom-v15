# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    picking_ids = fields.Many2many('stock.picking', compute='_compute_picking_ids', string='Pickings')

    @api.depends('invoice_line_ids.stock_move_ids.picking_id')
    def _compute_picking_ids(self):
        for rec in self:
            rec.picking_ids = rec.invoice_line_ids.mapped('stock_move_ids').mapped('picking_id')

    @api.multi
    def action_view_picking(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]

        pickings = self.mapped('picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action

    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        if not self:
            return res
        stock_picking = self.env['stock.picking']
        for pick in self.mapped('picking_ids').filtered(lambda pick: pick.state != 'done'):
            if pick._check_backorder():
                move_info = pick.move_ids_without_package.filtered(
                    lambda m: m.quantity_done < m.product_uom_qty)
                product_info = move_info.mapped('product_id')
                if product_info and not all([m.reason_id for m in move_info]):
                    msg = '⚠ 𝐘𝐨𝐮 𝐧𝐞𝐞𝐝 𝐭𝐨 𝐞𝐧𝐭𝐞𝐫 𝐭𝐡𝐞 𝐬𝐭𝐨𝐜𝐤 𝐫𝐞𝐭𝐮𝐫𝐧 𝐫𝐞𝐚𝐬𝐨𝐧 𝐟𝐨𝐫 𝐏𝐫𝐨𝐝𝐮𝐜𝐭 in DO %s\n' % pick.name
                    for i, product in enumerate(product_info, 1):
                        msg += '\t\t%d. %s\n' % (i, product.display_name)
                    raise UserError(_(msg))
                stock_picking |= pick
            else:
                pick.action_done()
        wiz = self.env['stock.backorder.confirmation'].create({'pick_ids': [(4, p.id) for p in stock_picking]})
        wiz.process_cancel_backorder()
        return res


AccountInvoice()


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    stock_move_ids = fields.Many2many('stock.move', string="Stock Moves")


AccountInvoiceLine()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
