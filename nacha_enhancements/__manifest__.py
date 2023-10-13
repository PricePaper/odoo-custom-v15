

{
    'name': 'Nacha Enhancements',
    'version': '1',
    'summary': 'Nacha Enhancements',
    'description': """
Nacha Enhancements
=======================
Modifying l10n_us_payment_nacha module
    """,
    'author': 'Confianz Global',
    'depends': ['l10n_us_payment_nacha','account_batch_payment', 'l10n_us', 'account'],
    'sequence': 1700,
    'demo': [
    ],
    'data': [
        'views/account_journal_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
