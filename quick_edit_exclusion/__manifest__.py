# -*- encoding: utf-8 -*-
##############################################################################
#
#    Confianz IT
#    Copyright (C) 2022   (https://www.confianzit.com)
#
##############################################################################


{
    'name': "Quick Edit Exclusion",
    'version': '15.0.1.0',
    'category': 'web',
    'sequence': '15',
    'description': "",
    'author': 'vishnu.m@confianzit.biz',
    'website': 'https://www.confianzit.com',
    'license': 'LGPL-3',
    'depends': ['web'],
    'data': [],
    'demo': [],
    'assets': {
        'web.assets_backend': [
            '/quick_edit_exclusion/static/src/js/form_renderer.js',
            '/quick_edit_exclusion/static/src/js/list_renderer.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
