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
        'views/delivery_view.xml'
    ],
     'assets': {
        'web.assets_frontend': [
            '/website_base/static/src/lib/sweetalert2/sweet.js',
            '/website_base/static/src/js/main.js'
        ],
     },
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}


