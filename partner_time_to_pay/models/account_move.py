# Copyright 2022 - Moduon
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
import logging
_log = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"

    full_reconcile_payment_date = fields.Date(
        string="Payment Date",
        compute="_compute_full_reconcile_payment_date",
        # store=True,
        compute_sudo=True,
        help="Date when the complete reconciliation of this invoice occurred.",
        # default = False
    )

    @api.depends("payment_state")
    def _compute_full_reconcile_payment_date(self):
        aml_model = self.env["account.move.line"]
        in_payment_states = {"paid", "in_payment"}


        selected_invoices = self.filtered(lambda inv: inv.payment_state in in_payment_states and not inv.full_reconcile_payment_date)

        rest = self - selected_invoices
        rest.full_reconcile_payment_date = False

        _log.info(f"===================={selected_invoices}")
        new_moves = self.env["account.move"]
        for move in selected_invoices:
            # if move.payment_state in in_payment_states and not move.full_reconcile_payment_date:
                # if not move.full_reconcile_payment_date :
            valid_accounts = move.line_ids.filtered(lambda ml: ml.account_id.user_type_id.type in {"receivable", "payable"}).mapped("account_id")
            reconciled_moves = (
                aml_model.search(
                    [
                        ("account_id", "in", valid_accounts.ids),
                        ("parent_state", "=", "posted"),
                        ("partner_id", "=", move.commercial_partner_id.id),
                        ("reconciled", "=", True),
                        ("id", "not in", move.line_ids.ids),
                        (
                            "full_reconcile_id.reconciled_line_ids",
                            "in",
                            move.line_ids.ids,
                        ),
                    ],order="date"
                )
                .mapped("move_id")
                
            )
            if reconciled_moves[-1:].date:
                move.full_reconcile_payment_date = reconciled_moves[-1:].date
            else:
                new_moves = new_moves.union(move)
                # contin
        else:
            new_moves.full_reconcile_payment_date = False
            #  .full_reconcile_payment_date = None
            # self.env.cr.commit()
