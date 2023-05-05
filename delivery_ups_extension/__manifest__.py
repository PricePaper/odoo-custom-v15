# -*- coding: utf-8 -*-
{
    'name': 'UPS Extension',
    'version': '15.0.0',
    'license': 'LGPL-3',
    'summary': 'UPS Extension',
    'author': 'Confianz',
    'website': 'https://www.confianzit.com',
    'description': """
    UPS integration extension for PPT
    """,
    'data': ['views/sale_order.xml'],
    'depends': [
        'delivery_ups', 'sale_margin', 'price_paper'
    ],
    'installable': True,
    'application': False,
}
