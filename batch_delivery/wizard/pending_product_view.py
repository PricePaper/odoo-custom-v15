# -*- coding: utf-8 -*-

from odoo import fields, models, api


class PendingProductView(models.TransientModel):
    _name = 'pending.product.view'
    _description = 'Pending Product View'

    batch_ids = fields.Many2many("stock.picking.batch", string='Batch List')
    picking_ids = fields.Many2many('stock.picking', string='Pick List')
    pending_line_ids = fields.One2many('pending.product.email.view', 'wiz_id', string='Pending List')

    def generate_move_lines(self):
        """
        Extract the pickings from batch and filtered out the pending move lines.
        """
        records = self.batch_ids.mapped('picking_ids') if self.batch_ids else self.picking_ids
        move_lines = records.filtered(lambda pick: pick.state not in ['done', 'cancel']).mapped('move_lines').ids
        action = self.env['ir.actions.act_window'].for_xml_id('batch_delivery', 'stock_move_pending_product_action')
        action['domain'] = [('id', 'in', move_lines)]
        return action

    def generate_mails(self):
        """
        generate emails for individual (sales followers) who having pending product moves.
        """
        recipient_ids = self.pending_line_ids.mapped('followers')
        mail_template = self.env.ref('batch_delivery.email_price_paper_pending_product_mail')
        mail_group = {}
        for rep in recipient_ids:
            for move in self.pending_line_ids:
                if rep in move.followers:
                    mail_group.setdefault(rep, []).append(move)
        for rep, moves in mail_group.items():
            mail_template.with_context({'summery_list': moves, 'partner_email': rep.email}).send_mail(rep.id,
                                                                                                      force_send=True)


class PendingProductLineView(models.TransientModel):
    _name = 'pending.product.email.view'
    _description="Pending Product Email"

    product_id = fields.Many2one('product.product', string='Product')
    product_uom_qty = fields.Float(string="Product Quantity")
    reserved_available_qty = fields.Float(string="Available Quantity")
    product_uom = fields.Many2one('uom.uom', string="Product UOM")
    note = fields.Text(string="Note")
    followers = fields.Many2many('res.partner', string="Followers")
    same_product_ids = fields.Many2many('product.product', string="Alternative Products")
    wiz_id = fields.Many2one('pending.product.view')
    picking_id = fields.Many2one('stock.picking', string='Source')




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
