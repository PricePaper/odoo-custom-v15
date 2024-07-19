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
                'website', 'contacts', 'helpdesk','theme_pricepaper','sign'],
    'sequence': 1700,
    'demo': [
    ],
    'data': [
        'security/portal_enhancements_security.xml',
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'views/res_partner_views.xml',
        'views/portal_model_access_config.xml',
        'wizard/add_portal_contacts.xml',
        'views/res_config.xml',
        'views/templates.xml',
        'views/website_onboarding.xml',
        'views/crm_lead.xml',
        'views/res_user_views.xml',
        'wizard/portal_access_view.xml',
        'wizard/add_portal_companies.xml',
        'wizard/crm_lead_to_opportunity_views.xml',
        'wizard/portal_approval.xml'

    ],
     'assets': {
        'web.assets_frontend': [
            'portal_enhancements/static/src/js/main.js',
            'portal_enhancements/static/src/scss/main.scss',


        ]
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
