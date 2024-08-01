# -*- encoding: utf-8 -*-
##############################################################################
#
#    Confianz IT
#    Copyright (C) 2022   (https://www.confianzit.com)
#
##############################################################################


{
    'name': "Price Paper Mobile APIs",
    'version': '1.0',
    'category': 'website',
    'sequence': '16',
    'description': "APIs for Price Paper mobile app",
    'website': 'https://www.confianzit.com',
    'license': 'LGPL-3',
    'author': 'Confianz Global',
    'depends': ['website_sale', 'price_paper', 'authorize_extension'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config.xml',
        'views/account_views.xml',
        'views/mobile_banner.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
