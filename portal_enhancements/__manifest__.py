# -*- coding: utf-8 -*-

{
    'name': 'Portal Enhancements',
    'version': '1',
    'summary': 'Portal Enhancements',
    'description': """
Portal Enhancements
=======================
Granting enhanced access to portal users
    """,
    'author': 'Confianz Global',
    'depends': ['base', 'sale', 'purchase', 'account', 'price_paper', 'calendar', 'partner_firstname', 'portal',
                'website', 'contacts', 'helpdesk','theme_pricepaper'],
    'sequence': 1700,
    'demo': [
    ],
    'data': [
        'security/portal_enhancements_security.xml',
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'wizard/add_portal_contacts.xml',
        'views/res_config.xml',
        'views/templates.xml',
        'views/website_onboarding.xml',
        'views/crm_lead.xml',
        'wizard/portal_access_view.xml',
        'wizard/add_portal_companies.xml',
        'wizard/crm_lead_to_opportunity_views.xml'

    ],
     'assets': {
        'web.assets_frontend': [
            'portal_enhancements/static/src/js/main.js',
            
            
        ]
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
