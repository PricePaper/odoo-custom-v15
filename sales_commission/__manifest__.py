# -*- coding: utf-8 -*-

{
    'name': 'Sales Commission',
    'version': '1.0',
    'license': 'LGPL-3',
    'category': 'Sales and Purchase',
    'summary': "Sales and Purchase",
    'description': """
Sales commission module implemented for Price Papers.
=================================================================
Sales commission module implemented for Price Papers.
       """,
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',
    'images': [],

    'data': [
        'data/data.xml',
        'data/account_data.xml',
        'data/ir_sequence_data.xml',
        'security/sales_commission_security.xml', #TODO security permission files pending to migate to 15
        'security/ir.model.access.csv',
        'wizard/existing_user.xml',
        'wizard/sales_commission.xml',
        'views/report_template.xml',
        'views/report_commission_audit.xml',
        'views/report_commission_settlement.xml',
        'views/sale_commission_settlement.xml',
        'views/sale_commission.xml',
        'views/saleorder_report.xml',
        'views/invoice_report.xml',
        'views/res_partner.xml',
        'views/crm_lead.xml',
        'views/account_invoice.xml',
        'views/commission_rules.xml',
        'views/commission_percentage.xml',
        'views/sale_view.xml',
        'views/res_company.xml',
        'views/menu.xml',
        'wizard/crm_lead_to_opportunity_views.xml'
    ],

    'depends': ['price_paper','price_maintanance'],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
