# coding: utf-8
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class AccountBatchPayment(models.Model):
    _inherit = "account.batch.payment"

    def _validate_journal_for_nacha(self):
        super(AccountBatchPayment, self)._validate_journal_for_nacha()
        journal = self.journal_id
        if not journal.nacha_company_chase_account:
            raise ValidationError(_(f"Please set a NACHA Company Discretionary Data (Chase account) on the {journal.display_name}s journal."))

    def _validate_payment_for_nacha(self, payment):
        super(AccountBatchPayment, self)._validate_payment_for_nacha(payment)
        if not payment.partner_id.vat:
            raise ValidationError(_("Please add a Tax ID (Individual Identification Number) to partner %s") % payment.partner_id.name)
        if payment.date <= fields.Date.today():
            raise ValidationError(
                _("The payment date of Payment %s must be at least one day after the batch payment creation date.") % payment.display_name)

    def _generate_nacha_header(self):
        header = []
        header.append("1")  # Record Type Code
        header.append("01")  # Priority Code
        header.append("{:>10.10}".format(self.journal_id.nacha_immediate_destination))  # Immediate Destination
        header.append("{:>10.10}".format(self.journal_id.nacha_immediate_origin))  # Immediate Origin
        header.append("{:6.6}".format(fields.Date.today().strftime("%y%m%d")))  # File Creation Date

        now_in_client_tz = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        header.append("{:4.4}".format(now_in_client_tz.strftime("%H%M")))  # File Creation Time

        nr = self.search_count([("id", "!=", self.id), ("date", "=", self.date)])
        header.append("{:1.1}".format(chr(min(90, ord("A") + nr))))  # File ID Modifier

        header.append("094")  # Record Size
        header.append("{:02d}".format(self._get_blocking_factor()))  # Blocking Factor
        header.append("1")  # Format Code
        header.append("{:23.23}".format(self.journal_id.nacha_destination))  # Destination

        formatted_company_name = ''.join(char.upper() if char.isalpha() else ' ' for char in self.journal_id.company_id.name)
        header.append("{:23.23}".format(formatted_company_name))  # Origin or Company Name

        # ideally this would be the display_name but it will be too long
        header.append("{:8d}".format(self.id))  # Reference Code

        return "".join(header)

    def _generate_nacha_batch_header_record(self, payment, batch_nr):
        batch = []
        batch.append("5")  # Record Type Code
        if self.batch_type == 'outbound':
            batch.append("220")  # Service Class Code (credits only)
        if self.batch_type == 'inbound':
            batch.append("225")  # Service Class Code (Debits only)
        formatted_company_name = ''.join(char.upper() if char.isalpha() else ' ' for char in self.journal_id.company_id.name)
        batch.append("{:16.16}".format(formatted_company_name))  # Company Name

        batch.append("{:0>20.20}".format(self.journal_id.nacha_company_chase_account))  # Company Discretionary Data
        batch.append("{:0>10.10}".format(self.journal_id.nacha_company_identification))  # Company Identification
        batch.append("CCD")  # Standard Entry Class Code

        formatted_reference = ''.join(char.upper() if char.isalpha() else char if char.isnumeric() else '' for char in payment.ref)
        batch.append("{:10.10}".format(formatted_reference))  # Company Entry Description

        batch.append("{:6.6}".format(payment.date.strftime("%y%m%d")))  # Company Descriptive Date
        batch.append("{:6.6}".format(payment.date.strftime("%y%m%d")))  # Effective Entry Date
        batch.append("{:3.3}".format(""))  # Settlement Date (Julian)
        batch.append("1")  # Originator Status Code
        batch.append("{:8.8}".format(self.journal_id.nacha_origination_dfi_identification))  # Originating DFI Identification
        batch.append("{:07d}".format(batch_nr))  # Batch Number

        return "".join(batch)

    def _generate_nacha_entry_detail(self, payment):
        bank = payment.partner_bank_id
        entry = []
        entry.append("6")  # Record Type Code (PPD)
        if self.batch_type == 'outbound':
            entry.append("22")  # Transaction Code (credits only)
        if self.batch_type == 'inbound':
            entry.append("27")  # Transaction Code (Debits only)
        entry.append("{:8.8}".format(bank.aba_routing[:-1]))  # RDFI Routing Transit Number
        entry.append("{:1.1}".format(bank.aba_routing[-1]))  # Check Digit
        entry.append("{:17.17}".format(bank.acc_number))  # DFI Account Number
        entry.append("{:010d}".format(round(payment.amount * 100)))  # Amount

        formatted_individual_id_num = ''.join(char.upper() if char.isalpha() else char if char.isnumeric() else '' for char in payment.partner_id.vat)
        entry.append("{:15.15}".format(formatted_individual_id_num))  # Individual Identification Number

        formatted_individual_name = ''.join(char.upper() if char.isalpha() else ' ' for char in payment.partner_id.name)
        entry.append("{:22.22}".format(formatted_individual_name))  # Individual Name

        entry.append("  ")  # Discretionary Data Field
        entry.append("0")  # Addenda Record Indicator

        # trace number
        entry.append("{:8.8}".format(self.journal_id.nacha_origination_dfi_identification))  # Trace Number (80-87)
        entry.append("{:07d}".format(0))  # Trace Number (88-94)

        return "".join(entry)

    def _generate_nacha_batch_control_record(self, payment, batch_nr):
        bank = payment.partner_bank_id
        control = []
        control.append("8")  # Record Type Code
        if self.batch_type == 'outbound':
            control.append("220")  # Service Class Code (credits only)
        if self.batch_type == 'inbound':
            control.append("225")  # Service Class Code (Debits only)
        control.append("{:06d}".format(1))  # Entry/Addenda Count
        control.append("{:010d}".format(self._calculate_aba_hash(bank.aba_routing)))  # Entry Hash
        control.append("{:012d}".format(0))  # Total Debit Entry Dollar Amount in Batch
        control.append("{:012d}".format(round(payment.amount * 100)))  # Total Credit Entry Dollar Amount in Batch
        control.append("{:0>10.10}".format(self.journal_id.nacha_company_identification))  # Company Identification
        control.append("{:19.19}".format(""))  # Message Authentication Code (leave blank)
        control.append("{:6.6}".format(""))  # Reserved (leave blank)
        control.append("{:8.8}".format(self.journal_id.nacha_origination_dfi_identification))  # Originating DFI Identification
        control.append("{:07d}".format(batch_nr))  # Batch Number

        return "".join(control)
