# -*- encoding: utf-8 -*-
##############################################################################
#
#    Confianz IT
#    Copyright (C) 2021   (https://www.confianzit.com)
#
##############################################################################

{
    'name': 'Price Paper Report',
    'version': '1.0',
    'license': 'LGPL-3',
    'category': 'Sales and Purchase',
    'summary': "Reports for Pricepaper",
    'description': """
Custom module implemented for Price Papers Reports.
=================================================================
Custom module implemented for Price Paper Reports.
       """,
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',
    'images': [],

    'data': [
        'views/sale_report.xml',
        'views/purchase_report.xml',
    ],


    'depends': ['instant_invoice'],

    'installable': True,
    'auto_install': False,
    'application': False,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
