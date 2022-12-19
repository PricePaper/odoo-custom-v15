# -*- encoding: utf-8 -*-
##############################################################################
#
#    Confianz IT
#    Copyright (C) 2021   (https://www.confianzit.com)
#
##############################################################################
{
    'name': 'Product_Barcode',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Product Barcode',
    'author': 'Confianz',
    'summary': 'Product Barcode',
    'description': """
Custom module implemented for Price Papers Barcode process.
===========================================================

    """,
    'installable': True,
    'application': False,
    'depends': ['rt_widget_qr_cam', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/product_barcode_wizard.xml',
        'views/product_product.xml',
    ],
}
