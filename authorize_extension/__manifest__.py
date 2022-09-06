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
        'wizard/generate_payment_token_view.xml',
        'views/res_partner.xml',
        'views/account_payment_term_view.xml',
        'views/account_fiscal_position.xml',
        'views/sale_order_view.xml',
        'security/ir.model.access.csv',
    ],
    'depends': [
        'base', 'payment', 'accounting_extension'
    ],
    'installable': True,
    'application': True,
}
