# -*- encoding: utf-8 -*-
##############################################################################
#
#    Confianz IT
#    Copyright (C) 2019   (https://www.confianzit.com)
#
##############################################################################


{
    'name': 'Confianz Theme',
    'version': '12.0.1.0',
    'license': 'LGPL-3',
    'category': 'Theme',
    'sequence': '3',
    'description': """
        New theme for Odoo.
    """,
    'author': 'Confianz IT',
    'website': 'https://www.confianzit.com',
    'depends': ['web_enterprise'],
    'data': [
#        'views/assets.xml',
    ],
    'assets': {
        'web.assets_backend': ['/odoov12_theme/static/src/css/odoov12_theme.css'],
        'web_enterprise._assets_primary_variables' : ['/odoov12_theme/static/src/scss/primary_variables.scss'],
        'web_enterprise._assets_secondary_variables' : ['/odoov12_theme/static/src/scss/secondary_variables.scss']
        },
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
