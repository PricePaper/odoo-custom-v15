# -*- coding: utf-8 -*-
{
    'name': 'Sales Analysis Report',
    'version': '1.0',
    'license': 'LGPL-3',
    'summary': 'Sales Analysis Report',
    'description': """
Sales Analysis Report
=================================
    """,
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',

    'data': [
        'security/ir.model.access.csv',
        'report/sales_analysis_report.xml'
    ],
    'depends': ['sale_management', 'account', 'price_paper'],
    'installable': True,
    'application': False,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
