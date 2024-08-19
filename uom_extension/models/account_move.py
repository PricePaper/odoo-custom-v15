from odoo import fields, models, api


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super()._onchange_product_id()
        if self.product_id:
            self.product_uom_id = self.product_id.ppt_uom_id
        return res

    def _sale_can_be_reinvoice(self):
        self.ensure_one()
        return not self.is_anglo_saxon_line and super(AccountMoveLine, self)._sale_can_be_reinvoice()

    def _stock_account_get_anglo_saxon_price_unit(self):

        self.ensure_one()
        if not self.product_id:
            return self.price_unit
        original_line = self.move_id.reversed_entry_id.line_ids.filtered(lambda l: l.is_anglo_saxon_line
                                                                                   and l.product_id == self.product_id and l.product_uom_id == self.product_uom_id and l.price_unit >= 0)
        original_line = original_line and original_line[0]
        price_unit = original_line.price_unit if original_line \
            else self.product_id.with_company(self.company_id)._stock_account_get_anglo_saxon_price_unit(uom=self.product_uom_id)
        so_line = self.sale_line_ids and self.sale_line_ids[-1] or False
        if so_line:
            is_line_reversing = bool(self.move_id.reversed_entry_id)
            qty_to_invoice = self.product_uom_id._compute_quantity(self.quantity, self.product_id.uom_id)
            account_moves = so_line.invoice_lines.move_id.filtered(lambda m: m.state == 'posted' and bool(m.reversed_entry_id) == is_line_reversing)
            posted_cogs = account_moves.line_ids.filtered(lambda l: l.is_anglo_saxon_line and l.product_id == self.product_id and l.balance > 0)
            qty_invoiced = sum([line.product_uom_id._compute_quantity(line.quantity, line.product_id.uom_id) for line in posted_cogs])
            value_invoiced = sum(posted_cogs.mapped('balance'))

            product = self.product_id.with_company(self.company_id).with_context(is_returned=is_line_reversing, value_invoiced=value_invoiced)
            average_price_unit = product._compute_average_price(qty_invoiced, qty_to_invoice, so_line.move_ids)
            if average_price_unit:
                price_unit = self.product_id.ppt_uom_id.with_company(self.company_id)._compute_price(average_price_unit, self.product_uom_id)
        return price_unit
