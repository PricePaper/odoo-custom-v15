# -*- encoding: utf-8 -*-
##############################################################################
#
#    Confianz IT
#    Copyright (C) 2022   (https://www.confianzit.com)
#
##############################################################################


{
    'name': "Batch Payment Matching",
    'version': '15.0.1.0',
    'category': 'Accounting',
    'sequence': '15',
    'description': "",
    'author': 'vishnu.m@confianzit.biz',
    'website': 'https://www.confianzit.com',
    'license': 'LGPL-3',
    'depends': ['web', 'account_batch_payment'],
    'data': [],
    'demo': [],
    'assets': {
        'web.assets_backend': [
            '/batch_payment_match/static/src/js/batch_payment_match.js',
        ],
        'web.assets_qweb': [
            '/batch_payment_match/static/src/xml/batch_payment_match.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
