# -*- encoding: utf-8 -*-
##############################################################################
#
#    Confianz IT
#    Copyright (C) 2021   (https://www.confianzit.com)
#
##############################################################################

{
    'name': 'Disable Quick Create',
    'version': '1.0',
    'license': 'LGPL-3',
    'category': 'web',
    'summary': "Web Assets",
    'description': """
Custom module implemented for Many2one drop down quick create.
=====================================================================
This module disable the quick create from odoo many2one drop down.
       """,
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',
    'images': [],
    'data': ['security/quick_create_security.xml',],
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            'quick_create_disable/static/src/js/many2one_quick_create_disbale.js',
        ],
    },
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
