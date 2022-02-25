# -*- coding: utf-8 -*-

{
    'name': "CRM Enhancements",

    'summary': """
        Creates a revenue forcasting view in the partners kanban view based on their expected revenue and seasonal revenue.
    """,

    'description': """
        Creates a revenue forcasting view in the partners kanban view based on their expected revenue and seasonal revenue.
    """,

    'author': 'Confianz Global',
    'website': 'http://confianzit.com',

    'category': 'CRM',
    'version': '15.0.0.1',
    'license': 'LGPL-3',
    'depends': ['crm', 'sale', 'price_paper'],

    'data': [
        'data/data.xml',
        'views/res_partner.xml',
        # 'views/crm_lead.xml',
        'views/res_company.xml',
        'wizard/crm_lead_to_opportunity_views.xml'
    ],

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
