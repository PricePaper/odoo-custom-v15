# -*- coding: utf-8 -*-

{
    'name': 'Price Paper Batch Delivery',
    'version': '1.0',
    'license': 'LGPL-3',
    'category': 'Delivery',
    'summary': "Sales and Purchase",
    'description': """
Custom module implemented for Price Papers Batch Delivery Process.
=====================================================================
This module sets up the batch delivery process for price paper.
       """,
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',
    'images': [],
    # TODO :: FIX THIS FOR ODOO-15 MIGRATION
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/truck_driver_view.xml',
       'views/account_view.xml',
        'wizard/assign_route_wizard_view.xml',
        'wizard/driver_invoice_wizard_view.xml',
        'wizard/picking_full_return_wizard_view.xml',
        'wizard/stock_backorder_confirmation_views.xml',
        'wizard/reset_quantity_view.xml',
        'wizard/so_cancel_reason.xml',
        'wizard/pending_product_view.xml',
        'views/truck_route_view.xml',
        'views/batch_delivery_view.xml',
        'views/product_view.xml',
        'views/stock_picking_return.xml',
        'views/stock_move.xml',
        'views/sale_view.xml',
        'views/batch_payment_common.xml',
        'views/delivery_carrier_view.xml',
        'views/partner_view.xml',
        'views/picking_product_pending.xml',
        'views/stock_location_view.xml',
       'views/stock_picking_view.xml',
        'views/website_asset.xml',
    ],
    'depends': [
        'price_paper',
        'stock_picking_batch',
        'base_geolocalize',
        'website_google_map',
        'website_customer',
        'account_reports',
        'stock_product_location',
        'account_batch_payment',
         'purchase_extension'
    ],
    'assets': {
        'web.assets_backend': [
                'batch_delivery/static/src/js/kanban_reset_button.js',
            ],
        'web.assets_qweb': [
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
