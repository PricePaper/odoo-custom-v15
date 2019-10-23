# -*- coding: utf-8 -*-

{
    'name': 'Instant Sale',
    'version': '1.0',
    'category': 'Sales and Purchase',
    'summary': "Sales and Purchase",
    'description': """
Custom module implemented for Instant sale for Price Papers.
       """,
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',
    'images': [],

    'depends': ['batch_delivery'],
    'data': [
                'views/sale_views.xml',
            ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
