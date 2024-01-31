# -*- encoding: utf-8 -*-
##############################################################################
#
#    Confianz IT
#    Copyright (C) 2022   (https://www.confianzit.com)
#
##############################################################################


{
    'name': "Website Base",
    'version': '1.0',
    'category': 'website',
    'sequence': '15',
    'description': "For managing the Website in accordance with backend",
    'website': 'https://www.confianzit.com',
    'license': 'LGPL-3',
    'depends': ['website_sale','price_paper'],
    'data': [
        'security/ir.model.access.csv',
        'views/templates.xml',
        # 'views/theme_templates.xml'
            
    ],
     'assets': {
        'web.assets_frontend': [
            # not needed cross button in discount we can use the default unreconcile method
            # keeping this for reference
            # '/accounting_extension/static/src/js/account_payment_field.js',
            
            '/website_base/static/src/lib/sweetalert2/sweet.js',
            '/website_base/static/src/js/main.js'
        ],
     },
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}


