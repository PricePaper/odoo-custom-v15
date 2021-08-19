
from odoo import fields, models, api
from odoo.exceptions import ValidationError


class BrowseLines(models.TransientModel):
    _name = 'browse.lines'
    _description = 'Browse Related Record Lines'

    rma_id = fields.Many2one("rma.ret.mer.auth", string="Rma")
    rma_type = fields.Selection(related="rma_id.rma_type", readonly=True)
    sale_id = fields.Many2one('sale.order', string="Sale Order")
    purchase_id = fields.Many2one('purchase.order', string="Purchase Order")
    picking_id = fields.Many2one('stock.picking', string="Picking")
    line_ids = fields.One2many("browse.lines.source.line", 'browse_id')

    def add_lines(self):
        if self.sale_id:
            lines = self.line_ids.filtered(lambda r: r.select)
            if not lines:
                raise ValidationError('There is no selected lines for process.')
            return self.add_sale_line(lines)
        elif self.purchase_id:
            lines = self.line_ids.filtered(lambda r: r.select)
            if not lines:
                raise ValidationError('There is no selected lines for process.')
            return self.add_purchase_line(lines)
        else:
            lines = self.line_ids.filtered(lambda r: r.select)
            if not lines:
                raise ValidationError('There is no selected lines for process.')
            return self.add_move_lines(lines)

    def add_sale_line(self, lines):
        order_line_lst = []
        for order_line in lines:
            rma_sale_line = (0, 0, {
                'product_id': order_line.product_id and order_line.product_id.id or False,
                'total_qty': order_line.total_qty or 0,
                'delivered_quantity': order_line.delivered_quantity,
                'order_quantity': order_line.order_quantity or 0,
                'refund_qty': order_line.refund_qty,
                'refund_price': order_line.refund_price,
                'rma_id': self.rma_id.id,
                'price_unit': order_line.price_unit or 0,
                'price_subtotal': order_line.price_subtotal or 0,
                'source_location_id': order_line.source_location_id and order_line.source_location_id.id,
                'destination_location_id': order_line.destination_location_id and order_line.destination_location_id.id,
                'type': order_line.type,
                'tax_id': [(6, 0, order_line.tax_id.ids)],
                'so_line_id': order_line.so_line_id.id,
                'product_uom': order_line.product_uom.id,
                'reason_id': order_line.reason_id and order_line.reason_id.id or False,
                'return_product_uom': order_line.return_product_uom.id,
                'dummy_product_uom': [(6, 0, order_line.dummy_product_uom.ids)]
            })
            order_line_lst.append(rma_sale_line)
        else:
            self.rma_id.write({'rma_sale_lines_ids': order_line_lst})

    def add_purchase_line(self, lines):
        po_line_lst = []
        for order_line in lines:
            rma_purchase_line = (0, 0, {
                'product_id': order_line.product_id and order_line.product_id.id or False,
                'total_qty': order_line.total_qty or 0,
                'refund_qty': order_line.refund_qty or 0,
                'refund_price': order_line.refund_price,
                'rma_id': self.rma_id.id,
                'order_quantity': order_line.order_quantity or 0,
                'delivered_quantity': order_line.delivered_quantity,
                'total_price': order_line.total_price,
                'price_unit': order_line.price_unit or 0,
                'source_location_id': order_line.source_location_id and order_line.source_location_id.id,
                'destination_location_id': order_line.destination_location_id and order_line.destination_location_id.id,
                'type': order_line.type,
                'tax_id': [(6, 0, order_line.tax_id.ids)],
                'po_line_id': order_line.po_line_id.id,
                'product_uom': order_line.product_uom.id,
                'reason_id': order_line.reason_id and order_line.reason_id.id or False,
                'return_product_uom': order_line.return_product_uom.id,
                'dummy_product_uom': [(6, 0, order_line.dummy_product_uom)]
            })
            po_line_lst.append(rma_purchase_line)
        else:
            self.rma_id.write({'rma_purchase_lines_ids': po_line_lst})

    def add_move_lines(self, lines):
        order_line_lst = []
        for order_line in lines:
            if self.rma_type == 'picking':
                move = self.env['stock.move'].search([
                    ('picking_id', '=', self.rma_id.id),
                    ('product_id', '=', order_line.product_id.id)])
                taxes = False
                if move.picking_id.rma_id.rma_type == 'customer':
                    line = self.env['rma.sale.lines'].search([
                        ('exchange_product_id', '=', order_line.product_id.id),
                        ('rma_id', '=', move.rma_id.id)])
                    taxes = line.tax_id
                if move.picking_id.rma_id.rma_type == 'supplier':
                    line = self.env['rma.purchase.lines'].search([
                        ('exchange_product_id', '=', order_line.product_id.id),
                        ('rma_id', '=', move.rma_id.id)])
                    taxes = line.tax_id
            if self.rma_type == 'lot':
                move = self.env['stock.move'].search([
                    ('picking_id', '=', self.picking_rma_id.id),
                    ('product_id', '=', order_line.product_id.id)])
                taxes = []
                if move.picking_id.rma_id.rma_type == 'customer':
                    line = self.env['rma.sale.lines'].search(
                        [('product_id', '=', order_line.product_id.id),
                         ('rma_id', '=', move.rma_id.id)])
                    taxes = line.tax_id
                if move.picking_id.rma_id.rma_type == 'supplier':
                    line = self.env['rma.purchase.lines'].search(
                        [('product_id', '=', order_line.product_id.id),
                         ('rma_id', '=', move.rma_id.id)])
                    taxes = line.tax_id
            rma_pick_line = (0, 0, {
                'product_id': order_line.product_id and order_line.product_id.id or False,
                'product_uom': order_line.product_uom.id,
                'dummy_product_uom': [(6, 0, order_line.product_id.sale_uoms.ids)],
                'reason_id': order_line.reason_id and order_line.reason_id.id or False,
                'return_product_uom': order_line.product_uom.id,
                'total_qty': order_line.total_qty or 0,
                'delivered_quantity': order_line.delivered_quantity,
                'order_quantity': order_line.order_quantity or 0,
                'refund_qty': order_line.refund_qty,
                'rma_id': self.rma_id.id,
                'refund_price': order_line.refund_price,
                'price_unit': order_line.price_unit or 0,
                'source_location_id': order_line.source_location_id and order_line.source_location_id.id,
                'destination_location_id': order_line.destination_location_id and order_line.destination_location_id.id,
                'type': order_line.type,
                'tax_id': [(6, 0, order_line.tax_id.ids or [])]
            })
            order_line_lst.append(rma_pick_line)
        else:
            self.rma_id.write({'rma_picking_lines_ids': order_line_lst})


class BrowseLinesSourceLine(models.TransientModel):
    _name = 'browse.lines.source.line'
    _description = 'Related Source Lines'

    @api.depends('refund_qty', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """Compute the amounts of the SO line."""
        for line in self:
            refund_qty = line.refund_qty
            price = line.price_unit

            taxes = line.tax_id.compute_all(
                price, line.browse_id.rma_id.currency_id,
                refund_qty,
                product=line.product_id,
                partner=line.browse_id.rma_id.partner_id
            )

            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'refund_price': refund_qty * price
            })

    @api.model
    def _get_source_location(self):
        return self.env.user.company_id.source_location_id or \
               self.env['stock.location']

    @api.model
    def _get_destination_location(self):
        return self.env.user.company_id.destination_location_id or \
               self.env['stock.location']

    select = fields.Boolean(string=' ')
    so_line_id = fields.Many2one('sale.order.line')
    po_line_id = fields.Many2one('purchase.order.line')
    product_id = fields.Many2one('product.product', string='Product')
    reason_id = fields.Many2one("rma.reasons", string="Reason")
    reason = fields.Text(string="Reason")
    currency_id = fields.Many2one(
        "res.currency",
        related='browse_id.rma_id.partner_id.property_product_pricelist.currency_id',
        string='Currency',
        readonly=True)
    total_qty = fields.Float(
        string='Total Qty', readonly=False)
    order_quantity = fields.Float('Ordered Qty')
    delivered_quantity = fields.Float('Delivered Qty')
    price_unit = fields.Float('Unit Price')
    refund_qty = fields.Float('Return Qty')
    refund_price = fields.Float(compute='_compute_amount', string='Refund Price', )
    total_price = fields.Float(string='Total Price')
    type = fields.Selection([('return', 'Return'), ('exchange', 'Exchange')], string='Action', default='return')
    price_subtotal = fields.Float(compute='_compute_amount', string='Subtotal', readonly=True)
    price_tax = fields.Float(compute='_compute_amount', string='Taxes', readonly=True)
    price_total = fields.Float(compute='_compute_amount', string='Total', readonly=True)
    source_location_id = fields.Many2one('stock.location','Source Location', default=_get_source_location)
    destination_location_id = fields.Many2one(
        'stock.location',
        'Destination Location',
        default=_get_destination_location
    )
    exchange_product_id = fields.Many2one('product.product', 'Exchange Product')
    browse_id = fields.Many2one('browse.lines')
    product_uom = fields.Many2one('uom.uom', readonly=True)
    dummy_product_uom = fields.Many2many('uom.uom', readonly=True)
    return_product_uom = fields.Many2one('uom.uom')
    tax_id = fields.Many2many('account.tax', string='Taxes')


    @api.onchange('refund_qty', 'total_qty')
    def onchange_refund_price(self):
        for order in self:
            if order.total_qty != 0.0 and order.refund_qty > order.total_qty:
                raise ValidationError(('Refund Quantity should not be greater \
                      than Total Quantity.'))
            if order.refund_qty <= 0:
                raise ValidationError(('Refund Quantity should be greater than\
                  Zero'))
            if order.refund_qty > order.delivered_quantity:
                raise ValidationError(('Refund Quantity should not be greater \
                  than delivered quantity'))
            total_qty_amt = 0.0
            if order.total_price and order.total_qty:
                total_qty_amt = (order.total_price /
                                 order.total_qty) * float(order.refund_qty)
                order.refund_price = total_qty_amt
            else:
                if order.product_id and order.product_id.id:
                    order.refund_price = order.product_id.lst_price * order.refund_qty
        else:
            return {}
