# -*- coding: utf-8 -*-
{
    'name': 'Authorize.Net',
    'version': '15.0.0',
    'license': 'LGPL-3',
    'summary': 'Authorize.Net',
    'author': 'Confianz',
    'website': 'https://www.confianzit.com',
    'description': """
    Authorize.Net integration for PPT
    """,
    'data': [
        'data/data.xml',
        'wizard/generate_payment_token_view.xml',
        'wizard/add_transaction_to_invoice.xml',
        'wizard/reauth_invoice_token.xml',
        'views/invoice_report.xml',
        'views/res_partner.xml',
        'views/res_config_setting_view.xml',
        'views/account_move.xml',
        'views/batch_payment.xml',
        'views/payment_receipt.xml',
        'views/account_payment.xml',
        'views/payment_acquirer.xml',
        'views/payment_transaction_form.xml',
        'views/account_journal.xml',
        'views/account_payment_token_view.xml',
        'views/account_payment_term_view.xml',
        'views/account_fiscal_position.xml',
        'views/sale_order_view.xml',
        'security/ir.model.access.csv',
    ],
    'depends': [
        'base', 'payment', 'accounting_extension', 'payment_authorize'
    ],
    'installable': True,
    'application': True,
}
