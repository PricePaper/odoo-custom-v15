# -*- coding: utf-8 -*-
{
    'name': 'Sale Margin Extension',
    'version': '15.0.0',
    'license': 'LGPL-3',
    'summary': 'Sale Margin Extension',
    'author': 'Confianz',
    'website': 'https://www.confianzit.com',
    'description': """
     Modifications to Sale Margin module for PPT
    """,
    'data': ['views/sale_order.xml'],
    'depends': [
        'sale_margin', 'price_paper'
    ],
    'installable': True,
    'application': False,
}
