# -*- encoding: utf-8 -*-
##############################################################################
#
#    Confianz IT
#    Copyright (C) 2019   (https://www.confianzit.com)
#
##############################################################################


{
    'name': 'Saleperson Payment Collection',
    'version': '12.0.1.0',
    'category': 'Sales & Accounting',
    'sequence': '15',
    'description': """
        This module will helps register payments from sales window.
    """,
    'author': 'Confianz IT',
    'website': 'https://www.confianzit.com',
    'depends': ['account', 'sale'],
    'data': [
        'wizard/register_payment_view.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
