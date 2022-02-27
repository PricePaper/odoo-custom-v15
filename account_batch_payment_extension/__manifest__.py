# -*- coding: utf-8 -*-

{
    'name': 'Account Batch Payment Extension',
    'version': '1.0',
    'license': 'LGPL-3',
    'category': 'Accounting',
    'description': """
Allows filtering Batch PaymentMoveLines
=======================================

Customization of odoo account batch payment

""",
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',
    'depends': ['account_batch_payment', 'batch_delivery'],
    'data': [
         'data/data.xml',
         'security/ir.model.access.csv',
         'security/account_batch_payment_extension_security.xml',
         'views/res_company.xml',
         'views/account_batch_payment.xml',
         'views/returned_check_process.xml'
    ],
    'assets': {
        'web.assets_backend': [
                'account_batch_payment_extension/static/src/js/reconciliation_alert.js',
            ],
        'web.assets_qweb': [
        ],
    },
    'demo': [],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
