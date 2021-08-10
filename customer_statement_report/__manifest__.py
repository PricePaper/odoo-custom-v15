# -*- coding: utf-8 -*-
{
    'name': 'Customer Statement Report',
    'version': '1.0',
    'summary': 'Customer Statement Report',
    'description': """
Customer Statement Report
=================================
    """,
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',

    'data': [
        'report/customer_statement_report.xml',
        'data/mail_data.xml',
        'wizard/customer_statement_wizard.xml',
        'views/res_partner_view.xml',
        'views/res_company.xml'
    ],
    'depends': ['sale_management', 'account'],
    'installable': True,
    'application': False,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
