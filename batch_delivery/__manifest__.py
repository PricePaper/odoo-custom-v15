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
        'data/mail_template.xml',
        'security/ir.model.access.csv',
        'security/price_paper_security.xml',
        'report/invoice_report_standard.xml',
        'report/report_stockpicking_operations.xml',
        'report/report_master_pick_ticket.xml',
        'report/report_batch_delivery_slip.xml',
        'report/report_product_label.xml',
        'report/report_picking_batch.xml',
        'report/invoice_without_payment.xml',
        'report/report_invoice_templates.xml',
        'report/report_batch_driver.xml',
        'report/reports.xml',
        'views/truck_driver_view.xml',
        'views/account_view.xml',
        'wizard/reset_picking.xml',
        'wizard/assign_route_wizard_view.xml',
        'wizard/stock_overprocessed_transfer_views.xml',
        'wizard/product_location_change.xml',
        'wizard/picking_full_return_wizard_view.xml',
        'wizard/stock_backorder_confirmation_views.xml',
        'wizard/reset_quantity_view.xml',
        'wizard/so_cancel_reason.xml',
        'wizard/pending_product_view.xml',
        'views/res_company_view.xml',
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
        'views/stock_valuation_layer_view.xml',
        'views/order_banner.xml',
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
        'purchase_extension',
        'account_followup',
    ],
    'assets': {
        'web.assets_backend': [

            'batch_delivery/static/src/js/kanban_reset_button.js',
            'batch_delivery/static/src/css/card_block_border.css',
        ],
        'web.assets_qweb': [
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
