from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class UpdateUnitPrice(models.TransientModel):
    _name = "update.unit.price"
    _description = "Update Unit Price"

    po_price_unit = fields.Float('Used Unit Price')
    new_price_unit = fields.Float('New Unit Price')
    purchase_line_id = fields.Many2one('purchase.order.line')

    @api.model
    def default_get(self, fields):
        vals = super(UpdateUnitPrice, self).default_get(fields)
        if self._context.get('active_id') and self._context.get('active_model') == 'purchase.order.line':
            price_unit = self.env['purchase.order.line'].browse(self._context.get('active_id')).price_unit
            vals.update({'po_price_unit': price_unit, 'purchase_line_id': self._context.get('active_id')})
        return vals

    def update_unit_price(self):
        def _get_line_write_vals(line, price_unit):
            vals = line._get_price_total_and_subtotal(price_unit=price_unit)
            vals.update(line._get_fields_onchange_subtotal(price_subtotal=vals.get('price_subtotal')))
            vals.update(line._get_fields_onchange_balance(price_subtotal=vals.get('price_subtotal'), force_computation=True))
            return [1, line.id, vals]

        self.ensure_one()
        # Check the price is valid
        if self.new_price_unit <= 0:
            raise ValidationError("Unit price cannot be zero")

        # Check if any invoice lines are in the 'posted' state
        if any(line.parent_state == 'posted' for line in self.purchase_line_id.invoice_lines):
            raise ValidationError("Cannot update the price of a posted invoice")

        # Update price unit for moves and stock valuation layers
        for move in self.purchase_line_id.move_ids:
            if self.new_price_unit != move.price_unit:
                price_unit = self.purchase_line_id.product_uom._compute_price(self.new_price_unit, move.product_uom)
                move.write({'price_unit': price_unit})
                for svl in move.stock_valuation_layer_ids:
                    svl_price_unit = self.purchase_line_id.product_uom._compute_price(self.new_price_unit, svl.uom_id)
                    svl.write({'unit_cost': svl_price_unit, 'value': svl_price_unit * svl.quantity})
                    if svl.account_move_id:
                        svl.account_move_id.button_draft()
                        # Update debit and credit values in account move lines
                        vals = [(1, line.id, {'debit': abs(svl.value) if line.debit else 0, 'credit': abs(svl.value) if line.credit else 0}) for line
                                in svl.account_move_id.line_ids]
                        svl.account_move_id.write({"line_ids": vals})
                        svl.account_move_id.action_post()
        # Update price unit and other fields for invoice lines
        for invoice_line in self.purchase_line_id.invoice_lines:
            price_unit = self.purchase_line_id.product_uom._compute_price(self.new_price_unit, invoice_line.product_uom_id)
            existing_terms_lines = invoice_line.move_id.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
            other_lines = invoice_line.move_id.line_ids - existing_terms_lines - invoice_line
            company_currency_id = (invoice_line.move_id.company_id or self.env.company).currency_id
            vals = [_get_line_write_vals(invoice_line, price_unit)]
            # Update price unit, subtotal, and other fields for invoice line
            total = sum(other_lines.mapped(lambda l: company_currency_id.round(l.balance)))
            total += vals[0][2].get('price_total')
            dr = vals[0][2].get('debit', 0) > 0
            term_line = _get_line_write_vals(existing_terms_lines, total)
            if dr and term_line[2].get('debit'):
                term_line[2].update({'debit': 0, 'credit': term_line[2].get('debit')})
            if not dr and term_line[2].get('credit'):
                term_line[2].update({'credit': 0, 'debit': term_line[2].get('credit')})
            vals.append(term_line)
            invoice_line.move_id.write({'line_ids': vals})
        # Update price unit for purchase line

        self.purchase_line_id.write({'price_unit': self.new_price_unit})
        # post message
        msg = "<b>" + _("Unit price has been updated.") + "</b><ul>"

        msg += "<li> %s: <br/>" % self.purchase_line_id.product_id.display_name
        msg += _(
            "Unit Price: %(old_price)s -> %(new_price)s",
            old_price=self.po_price_unit,
            new_price=self.new_price_unit
        ) + "<br/>"
        msg += "</ul>"
        self.purchase_line_id.order_id.message_post(body=msg)


UpdateUnitPrice()
