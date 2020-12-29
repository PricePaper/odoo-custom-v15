# -*- encoding: utf-8 -*-
##############################################################################
#
#    Confianz IT
#    Copyright (C) 2019   (https://www.confianzit.com)
#
##############################################################################


{
    'name': 'Purge old open credits',
    'version': '12.0.1.0',
    'category': 'Accounting',
    'sequence': '15',
    'description': """
        This module will helps to purge old open credits.
    """,
    'author': 'Confianz IT',
    'website': 'https://www.confianzit.com',
    'depends': ['account_cancel', 'price_paper'],
    'data': [
        'data/cron_data.xml',

        'views/res_company_view.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
