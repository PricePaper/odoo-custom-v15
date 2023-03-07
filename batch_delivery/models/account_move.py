# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import json
from collections import defaultdict
from odoo.tools import float_compare
from odoo.tools.misc import formatLang, format_date, get_lang
import re


class AccountMove(models.Model):
    _inherit = "account.move"

    picking_ids = fields.Many2many('stock.picking', compute='_compute_picking_ids', string='Pickings')
    picking_count = fields.Integer(string="Delivery Count", compute='_compute_picking_ids')
    invoice_has_outstanding = fields.Boolean(search="_search_has_outstanding")
    out_standing_credit = fields.Float(compute='_compute_out_standing_credit', string="Out Standing")
    private_partner = fields.Boolean(string='Is Private', default=False,related='partner_id.private_partner')
    is_customer_return = fields.Boolean(string='Customer Return')
    sale_default_message = fields.Html(related="company_id.sale_default_message", readonly=True)

    def _get_mail_template(self):
        """
        :return: the correct mail template based on the current move type
        """
        return (
            'account.email_template_edi_credit_note'
            if all(move.move_type == 'out_refund' for move in self)
            else 'batch_delivery.email_template_edi_invoices'
        )

    def action_invoice_sent(self):
        self.ensure_one()
        template = self.env.ref('batch_delivery.email_template_edi_invoice', False)
        report_template = self.env.ref('batch_delivery.ppt_account_selected_invoices_with_payment_mail_report')
        if template and report_template and template.report_template.id != report_template.id:
            template.write({'report_template': report_template.id})
        return super(AccountMove, self).action_invoice_sent()

    @api.depends('line_ids.stock_move_ids')
    def _compute_picking_ids(self):
        for rec in self:
            pickings = rec.invoice_line_ids.mapped('stock_move_id').mapped('picking_id').filtered(lambda r: r.state != 'cancel') or \
                       rec.invoice_line_ids.mapped('stock_move_ids').mapped('picking_id').filtered(lambda r: r.state != 'cancel')
            rec.picking_ids = pickings
            rec.picking_count = len(pickings)
        return {}

    def _compute_out_standing_credit(self):
        for rec in self:
            info = json.loads(rec.invoice_outstanding_credits_debits_widget)
            rec.out_standing_credit = 0
            if info:
                rec.out_standing_credit = sum(list(map(lambda r: r['amount'], info['content'])))

    def _search_has_outstanding(self, operator, value):
        if self._context.get('default_move_type') in ('out_invoice', 'in_refund'):
            account = self.env.user.company_id.partner_id.property_account_receivable_id.id
        elif self._context.get('default_move_type') in ('in_invoice', 'out_refund'):
            account = self.env.user.company_id.partner_id.property_account_payable_id.id
        else:
            return []
        domain = [
            ('account_id', '=', account),
            ('reconciled', '=', False),
            ('parent_state', '=', 'posted'),
            ('partner_id', '!=', False),
            '|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0)]
        if self._context.get('default_move_type') in ('out_invoice', 'in_refund'):
            domain.append(('balance', '<', 0.0))
        else:
            domain.append(('balance', '>', 0.0))
        partner_ids = self.env['account.move.line'].search(domain).mapped('partner_id').ids
        return [('partner_id', 'in', partner_ids), ('state', '=', 'posted')]

    def action_view_picking(self):
        action = self.sudo().env.ref('stock.action_picking_tree_all').read()[0]
        pickings = self.mapped('picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action

    def get_discount(self):
        """
        implemented in accounting extension module
        """
        pass

    @api.depends(
        'line_ids.profit_margin',
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id'
    )
    def calculate_gross_profit(self):
        """
        Compute the gross profit in invoice.
        """
        for move in self:
            if move.move_type not in ('out_invoice', 'out_refund'):
                move.gross_profit = 0
                continue
            if move.payment_state in ('paid', 'in_payment'):
                gross_profit = 0
                for line in move.invoice_line_ids:
                    gross_profit += line.profit_margin
                card_amount = 0
                for partial, amount, counterpart_line in move._get_reconciled_invoices_partials():
                    if counterpart_line.payment_id.payment_method_line_id.code == 'credit_card':
                        card_amount += amount
                if card_amount:
                    gross_profit -= card_amount * 0.03
                discount = move.get_discount()
                if discount:
                    gross_profit -= discount
                if move.move_type == 'out_refund':
                    if gross_profit < 0:
                        gross_profit = 0
                move.update({'gross_profit': round(gross_profit, 2)})

            else:
                gross_profit = 0
                for line in move.invoice_line_ids:
                    gross_profit += line.profit_margin
                if move.invoice_payment_term_id.discount_per > 0:
                    gross_profit -= move.amount_total * (move.invoice_payment_term_id.discount_per / 100)
                if move.move_type == 'out_refund':
                    if gross_profit < 0:
                        gross_profit = 0
                move.update({'gross_profit': round(gross_profit, 2)})

    def _compute_show_reset_to_draft_button(self):
        res = super()._compute_show_reset_to_draft_button()
        for move in self:
            move.show_reset_to_draft_button = not move.picking_ids.filtered(
                lambda rec: rec.state in ('done')) and self.env.user.has_group('account.group_account_manager')
        return res

    def name_get(self):
        result = []
        if self._context.get('from_batch_payment', False):
            for move in self:
                result.append((move.id, '%s ( %s )' % (move.name, move.amount_residual)))
            return result
        return super().name_get()

    def remove_zero_qty_line(self):
        """
        Remove all zero qty lines from invoice
        """
        for move in self.filtered(lambda rec: rec.is_sale_document()):
            move.invoice_line_ids.filtered(lambda rec: rec.quantity == 0 and rec.display_type == False).sudo().unlink()
            # if an invoice have only one line we need to make sure it's not a delivery charge.
            # if it's a delivery charge, remove it from invoice.
            if len(move.invoice_line_ids) == 1 and move.invoice_line_ids.mapped('sale_line_ids') and any(
                    move.invoice_line_ids.mapped('sale_line_ids').mapped('is_delivery')) and move.move_type == 'out_invoice':
                move.invoice_line_ids.sudo().unlink()

    def picking_done(self):
        stock_picking = self.env['stock.picking']
        for pick in self.picking_ids.filtered(lambda rec: rec.state not in ('cancel', 'done')):
            move_info = pick.move_lines.filtered(lambda m: m.quantity_done < m.product_uom_qty)
            if move_info.ids:
                pick.make_picking_done()
            else:
                pick.button_validate()
        stock_picking.make_picking_done()

    def _post(self, soft=True):
        """
        Override super method to check some custom conditions before posting a move
        """
        for move in self.filtered(lambda rec: rec.move_type in ('out_invoice', 'out_refund')):
            move.remove_zero_qty_line()
        # res = super()._post(soft)
        for move in self.filtered(lambda rec: rec.move_type in ('out_invoice', 'out_refund')):
            if move.picking_ids.filtered(lambda rec: rec.state not in ('cancel', 'done')):
                move.picking_done()
            move.line_ids.mapped('sale_line_ids').mapped('order_id').filtered(lambda rec: rec.storage_contract is False).action_done()

            if move.picking_ids.filtered(lambda rec: rec.state not in ('cancel', 'done')):
                move.picking_done()

            if move.picking_ids.filtered(lambda rec: rec.state not in ('cancel', 'done')):
                raise UserError(_('Picking is not in done state'))
        return super()._post(soft)

    def set_name_inv(self, name):
        try:
            for move in self:
                self.env.cr.execute("""UPDATE account_move SET name=%s WHERE id=%s""", (name, move.id))
                print("""UPDATE account_move SET name=%s WHERE id='%s'""" % (name, move.id))
            self.env.cr.commit()
            return True
        except:
            return False

    def set_payment_state_mig_error(self):
        if not self:
            self = self.search([('state', '=', 'posted'), ('move_type', '!=', 'entry'), ('payment_state', '=', 'not_paid')])
        for move in self:
            currency = move.company_id.currency_id
            new_pmt_state = 'not_paid'
            for line in move.line_ids:
                if move._payment_state_matters():
                    # === Invoices ===
                    total_to_pay = 0.0
                    total_residual = 0.0

                    if line.account_id.user_type_id.type in ('receivable', 'payable'):
                        # Residual amount.
                        total_to_pay += line.balance
                        total_residual += line.amount_residual

            if move._payment_state_matters() and move.state == 'posted':
                if currency.is_zero(move.amount_residual):
                    reconciled_payments = move._get_reconciled_payments()
                    if not reconciled_payments or all(payment.is_matched for payment in reconciled_payments):
                        new_pmt_state = 'paid'
                    else:
                        new_pmt_state = move._get_invoice_in_payment_state()
                elif currency.compare_amounts(total_to_pay, total_residual) != 0:
                    new_pmt_state = 'partial'

            if new_pmt_state == 'paid' and move.move_type in ('in_invoice', 'out_invoice', 'entry'):
                reverse_type = move.move_type == 'in_invoice' and 'in_refund' or move.move_type == 'out_invoice' and 'out_refund' or 'entry'
                reverse_moves = self.env['account.move'].search(
                    [('reversed_entry_id', '=', move.id), ('state', '=', 'posted'), ('move_type', '=', reverse_type)])

                # We only set 'reversed' state in cas of 1 to 1 full reconciliation with a reverse entry; otherwise, we use the regular 'paid' state
                reverse_moves_full_recs = reverse_moves.mapped('line_ids.full_reconcile_id')
                if reverse_moves_full_recs.mapped('reconciled_line_ids.move_id').filtered(
                        lambda x: x not in (reverse_moves + reverse_moves_full_recs.mapped('exchange_move_id'))) == move:
                    new_pmt_state = 'reversed'
            move.payment_state = new_pmt_state

    def action_switch_invoice_into_refund_credit_note(self):
        if any(move.move_type not in ('in_invoice', 'out_invoice') for move in self):
            raise ValidationError(_("This action isn't available for this document."))

        for move in self:
            move.write({'name' : '/'})
        return super(AccountMove, self).action_switch_invoice_into_refund_credit_note()

    @api.depends('posted_before', 'state', 'journal_id', 'date')
    def _compute_name(self):
        """
        Overriding generate sequence method to get a number on create
        only a single line chnage from super, but I can't do without fully overriding
        """

        def journal_key(move):
            return move.journal_id, move.journal_id.refund_sequence and move.move_type

        def date_key(move):
            return move.date.year, move.date.month

        grouped = defaultdict(  # key: journal_id, move_type
            lambda: defaultdict(  # key: first adjacent (date.year, date.month)
                lambda: {
                    'records': self.env['account.move'],
                    'format': False,
                    'format_values': False,
                    'reset': False
                }
            )
        )
        self = self.sorted(lambda m: (m.date, m.ref or '', m.id))
        highest_name = self[0]._get_last_sequence() if self else False

        # Group the moves by journal and month
        for move in self:
            if not highest_name and move == self[0] and not move.posted_before and move.date:
                # In the form view, we need to compute a default sequence so that the user can edit
                # it. We only check the first move as an approximation (enough for new in form view)
                pass
            # todo the below comment is the only change
            elif (move.name and move.name != '/'):  # or move.state != 'posted':
                try:
                    if not move.posted_before:
                        move._constrains_date_sequence()
                    # Has already a name or is not posted, we don't add to a batch
                    continue
                except ValidationError:
                    # Has never been posted and the name doesn't match the date: recompute it
                    pass
            group = grouped[journal_key(move)][date_key(move)]
            if not group['records']:
                # Compute all the values needed to sequence this whole group
                move._set_next_sequence()
                group['format'], group['format_values'] = move._get_sequence_format_param(move.name)
                group['reset'] = move._deduce_sequence_number_reset(move.name)
            group['records'] += move

        # Fusion the groups depending on the sequence reset and the format used because `seq` is
        # the same counter for multiple groups that might be spread in multiple months.
        final_batches = []
        for journal_group in grouped.values():
            journal_group_changed = True
            for date_group in journal_group.values():
                if (
                        journal_group_changed
                        or final_batches[-1]['format'] != date_group['format']
                        or dict(final_batches[-1]['format_values'], seq=0) != dict(date_group['format_values'], seq=0)
                ):
                    final_batches += [date_group]
                    journal_group_changed = False
                elif date_group['reset'] == 'never':
                    final_batches[-1]['records'] += date_group['records']
                elif (
                        date_group['reset'] == 'year'
                        and final_batches[-1]['records'][0].date.year == date_group['records'][0].date.year
                ):
                    final_batches[-1]['records'] += date_group['records']
                else:
                    final_batches += [date_group]

        # Give the name based on previously computed values
        for batch in final_batches:
            for move in batch['records']:
                move.name = batch['format'].format(**batch['format_values'])
                batch['format_values']['seq'] += 1
            batch['records']._compute_split_sequence()
        self.filtered(lambda m: not m.name).name = '/'


    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
        line_vals = super(AccountMove, self)._stock_account_prepare_anglo_saxon_out_lines_vals()
        if any(self.mapped('is_customer_return')):
            for line in line_vals:
                if line.get('debit') > 0:
                    product = self.env['product.product'].browse(line.get('product_id'))
                    move = self.browse(line.get('move_id'))
                    accounts = product.product_tmpl_id.get_product_accounts(fiscal_pos=move.fiscal_position_id)
                    debit_interim_account = accounts['stock_input']
                    line.update({'account_id': debit_interim_account.id})
        return line_vals


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    stock_move_ids = fields.Many2many(comodel_name='stock.move', compute="_get_stock_move_ids", string="Stock Moves")
    stock_move_id = fields.Many2one('stock.move', 'Stock Move', index=True)

    def _update_line_quantityy(self, values):
        moves = self.mapped('move_id')
        for move in moves:
            move_lines = self.filtered(lambda x: x.move_id == move)
            msg = "<b>" + _("Quantity has been updated.") + "</b><ul>"
            for line in move_lines:
                msg += "<li> %s: <br/>" % line.product_id.display_name
                msg += _(
                    "Quantity: %(old_qty)s -> %(new_qty)s",
                    old_qty=line.quantity,
                    new_qty=values["quantity"]
                ) + "<br/>"
            msg += "</ul>"
            move.message_post(body=msg)


    def write(self, vals):
        if 'quantity' in vals:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            self.filtered(
                lambda r: float_compare(r.quantity, vals['quantity'],
                                                              precision_digits=precision) != 0)._update_line_quantityy(vals)
        res = super(AccountMoveLine, self).write(vals)
        return res

    def _get_stock_move_ids(self):
        for line in self:
            line.stock_move_ids = []
            if line.move_id.move_type != 'entry' and line.sale_line_ids:
                if line.move_id.move_type == 'out_refund' and not line.move_id.rma_id:
                    line.stock_move_ids = False
                    continue
                line.stock_move_ids = [[6, 0, line.sale_line_ids.mapped('move_ids').ids]]


        return {}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
