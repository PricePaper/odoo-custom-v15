# -*- coding: utf-8 -*-

{
    'name': 'Accounting Extension',
    'version': '1.1',
    'license': 'LGPL-3',
    'category': 'Accounting',
    'summary': "Accounting Extension",
    'description': """
Accounting Extension
====================
User can choose invoice against payments

       """,
    'author': 'Confianz Global',
    'website': 'http://www.confianzit.com',
    'images': [],
    # TODO :: FIX THIS FOR ODOO-15 MIGRATION
    'data': ['views/payment_term_view.xml',
             'data/data.xml',
             'views/stock_picking_batch.xml',
             'views/account_payment_view.xml',
             'views/account_invoice_view.xml',
             'wizard/add_new_cash_collected_line_wizard.xml',
             'wizard/add_discount_view.xml',
             'security/ir.model.access.csv'

        ],
    'depends': ["l10n_us_check_printing", 'purchase_extension', 'price_paper', 'batch_delivery', 'account_reports','account_followup'],
    'installable': True,
    'application': False,
#    TODO uncomment this
    'assets': {
        'web.assets_backend': [
                '/accounting_extension/static/src/js/account_payment_field.js',
            ],
        'web.assets_qweb': [
            'accounting_extension/static/src/xml/account_payment.xml',
        ],
    },
    'qweb': [
        "static/src/xml/account_payment.xml",
    ],
}




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
