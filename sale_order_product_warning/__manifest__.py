# -*- coding: utf-8 -*-

{
    'name' : 'Sale order product Warning',
    'version' : '15.0.0.1',
    'sequence': 10,
    'description': """
        Sale order product Duplicate warning in order lines
     """,
    'author': 'Confianz Global,Inc.',
    'website': 'https://www.confianzit.com',
    'summary': 'Enhancement on views',
    'category': 'Extra Tools',
    'depends' : ['web','sale_management'],
    'data': [
      'views/sale_order_inherit_view.xml'
    ],
     'assets': {
        'web.assets_backend': [
            'sale_order_product_warning/static/src/js/sale_order_warning.js',
            
        ],
        
    },
    
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
