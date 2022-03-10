# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import json
from collections import defaultdict


class AccountMove(models.Model):
    _inherit = "account.move"

    picking_ids = fields.Many2many('stock.picking', compute='_compute_picking_ids', string='Pickings')
    picking_count = fields.Integer(string="Delivery Count", compute='_compute_picking_ids')
    invoice_has_outstanding = fields.Boolean(search="_search_has_outstanding")
    out_standing_credit = fields.Float(compute='_compute_out_standing_credit', string="Out Standing")

    def action_invoice_sent(self):
        self.ensure_one()
        template = self.env.ref('account.email_template_edi_invoice', False)
        report_template = self.env.ref('batch_delivery.ppt_account_selected_invoices_with_payment_report')
        if template and report_template and template.report_template.id != report_template.id:
            template.write({'report_template': report_template.id})
        return super(AccountMove, self).action_invoice_sent()

    @api.depends('line_ids.stock_move_ids')
    def _compute_picking_ids(self):
        for rec in self:
            pickings = rec.line_ids.mapped('stock_move_ids').mapped('picking_id')
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
                for line in move.line_ids:
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
                # if invoice.discount_from_batch:
                #     gross_profit -= invoice.discount_from_batch
                if move.move_type == 'out_refund':
                    if gross_profit < 0:
                        gross_profit = 0
                move.update({'gross_profit': round(gross_profit, 2)})

            else:
                gross_profit = 0
                for line in move.line_ids:
                    gross_profit += line.profit_margin
                if move.partner_id.payment_method == 'credit_card':
                    gross_profit -= move.amount_total * 0.03
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
            move.invoice_line_ids.filtered(lambda rec: rec.quantity == 0).sudo().unlink()
            # if an invoice have only one line we need to make sure it's not a delivery charge.
            # if it's a delivery charge, remove it from invoice.
            if len(move.invoice_line_ids) == 1 and move.invoice_line_ids.mapped('sale_line_ids') and any(
                    move.invoice_line_ids.mapped('sale_line_ids').mapped('is_delivery')):
                move.invoice_line_ids.sudo().unlink()

    def action_post(self):
        """
        Override super method to check some custom conditions before posting a move
        """
        res = super().action_post()
        for move in self.filtered(lambda rec: rec.move_type in ('out_invoice', 'out_refund')):
            move.remove_zero_qty_line()
            # if move.picking_ids.filtered(lambda rec: rec.state == 'cancel'):
            #     raise UserError(
            #         'There is a Cancelled Picking (%s) linked to this invoice.' % move.picking_ids.filtered(lambda rec: rec.state == 'cancel').mapped(
            #             'name'))
            if move.picking_ids.filtered(lambda rec: rec.state not in ('cancel', 'done')):
                move.picking_ids.filtered(lambda rec: rec.state not in ('cancel', 'done')).make_picking_done()
            move.line_ids.mapped('sale_line_ids').mapped('order_id').filtered(lambda rec: rec.storage_contract is False).action_done()
        return res

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


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    stock_move_ids = fields.Many2many(comodel_name='stock.move', compute="_get_stock_move_ids", string="Stock Moves")

    def _get_stock_move_ids(self):
        for line in self:
            line.stock_move_ids = []
            if line.move_id.move_type != 'entry' and line.sale_line_ids:
                line.stock_move_ids = [[6, 0, line.sale_line_ids.mapped('move_ids').ids]]
        return {}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: