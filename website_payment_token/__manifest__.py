# -*- encoding: utf-8 -*-
##############################################################################
#
#    Confianz IT
#    Copyright (C) 2022   (https://www.confianzit.com)
#
##############################################################################


{
    'name': "Website Payment Token",
    'version': '1.0',
    'category': 'website',
    'sequence': '15',
    'description': "For managing the payment tokens from front",
    'website': 'https://www.confianzit.com',
    'license': 'LGPL-3',
    'depends': ['website_base'],
    'data': [
        'views/portal_template.xml'        
    ],
    "assets":{
        "web.assets_frontend":[
            '/website_payment_token/static/src/js/main.js'
        ]
    },
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}


