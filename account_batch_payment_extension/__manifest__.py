# -*- coding: utf-8 -*-

{
    'name': 'Account Batch Payment Extension',
    'version': '1.0',
    'category': 'Accounting',
    'description': """
Allows filtering Batch PaymentMoveLines ..
==============================================================================

This module help to filter out the move lines from existing batch payments

""",
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',
    'depends': ['account_batch_payment', 'sales_commission'],
    'data': ['views/res_company.xml',],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
