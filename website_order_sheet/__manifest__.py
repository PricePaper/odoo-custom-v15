# -*- encoding: utf-8 -*-
##############################################################################
#
#    Confianz IT
#    Copyright (C) 2022   (https://www.confianzit.com)
#
##############################################################################


{
    'name': "Website Order Sheet",
    'version': '1.0',
    'category': 'website',
    'sequence': '15',
    'description': "For managing the Order Sheet Per User",
    'website': 'https://www.confianzit.com',
    'license': 'LGPL-3',
    'depends': ['website_base'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/add_purchase_history_to_so.xml',
        'views/sheet_view.xml',
        'views/partner.xml',
        'views/templates.xml',
        'views/portal_template.xml',
        
    ],
    "assets":{
        "web.assets_frontend":[
            'website_order_sheet/static/src/js/main.js',
            'website_order_sheet/static/src/js/product_search.js'
        ]
    },
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}


