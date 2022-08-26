# -*- encoding: utf-8 -*-
##############################################################################
#
#    Confianz IT
#    Copyright (C) 2022   (https://www.confianzit.com)
#
##############################################################################


{
    'name': "Web Search With AND",
    'version': '15.0.1.0',
    'category': 'web',
    'sequence': '15',
    'description': "Use AND conditions on omnibar search",
    'author': 'vishnu.m@confianzit.biz',
    'website': 'https://www.confianzit.com',
    'license': 'LGPL-3',
    'depends': ['web'],
    'data': [],
    'demo': [],
    'assets': {
        'web.assets_backend': [
            '/web_search_with_and/static/src/js/components/main.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
