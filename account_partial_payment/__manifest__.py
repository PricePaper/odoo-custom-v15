# -*- encoding: utf-8 -*-
{
    'name': 'Account partial payment',
    'version': '12.0',
    'license': 'AGPL-3',
    'author': 'Confianz Global,Inc.',
    'website': 'https://www.confianzit.com',
    'category': 'Accounting & Finance',
    'description': """
Module to pay multiple invoices partially
=========================================

You can define the amount of corresponding invoices to pay.
it will only pay the amount you choosed.
    """,
    'depends': ['account', 'payment'],
    'data': [       
        'security/ir.model.access.csv',
        "views/payment_term.xml",
        "views/account_payment_view.xml",
        "views/res_company_view.xml",
        "views/account_invoice_view.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
