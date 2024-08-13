# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Cod Payment Acquirer',
    'version': '2.0',
    'category': 'Accounting/Payment Acquirers',
    'summary': 'Payment Acquirer: Wire cod Implementation',
    'description': " ",  # Non-empty string to avoid loading the README file.
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_cod_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'auto_install': True,
    'uninstall_hook': 'uninstall_hook',
    'license': 'LGPL-3',
}
