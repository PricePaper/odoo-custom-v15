# -*- encoding: utf-8 -*-
##############################################################################
#
#    Confianz IT
#    Copyright (C) 2021   (https://www.confianzit.com)
#
##############################################################################

{
    'name': 'Price Paper',
    'version': '1.0',
    'license': 'LGPL-3',
    'category': 'Sales and Purchase',
    'summary': "Sales and Purchase",
    'description': """
Custom module implemented for Price Papers.
=================================================================
Custom module implemented for Price Paper.
       """,
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',
    'images': [],

    'data': [
        'security/price_paper_security.xml',
        'security/ir.model.access.csv',
        'data/fax_data.xml',
        'data/data.xml',
        'wizard/sale_warning.xml',
        'wizard/stock_picking_return.xml',
        'wizard/upload_pricelist.xml',
        'wizard/inactive_product_report_wizard.xml',
        'wizard/release_sale_order_view.xml',
        'wizard/inactive_customer_report_wizard.xml',
        'wizard/add_purchase_history_to_so.xml',
        'wizard/cost_change_percentage.xml',
        'wizard/create_sale_tax_history_wizard.xml',
        'wizard/sc_popup_window.xml',
        'views/saleorder_report.xml',
        'views/res_company.xml',
        'views/filters.xml',
        'views/stock_move.xml',
        'views/product_notes.xml',
        'views/product_price_log.xml',
        'views/purchase_order_line.xml',
        'views/sale_order.xml',
        'views/sale_history.xml',
        'views/sale_tax_history.xml',
        'views/res_partner.xml',
        'views/product.xml',
        'views/cost_change.xml',
        'views/product_pricelist.xml',
        'views/customer_product_price.xml',
        'views/zip_delivery_day.xml',
        'views/account_view.xml',
        'views/payment_term_view.xml',
        'views/delivery_carrier_view.xml',
        'views/helpdesk_team_view.xml',
        'views/product_category.xml',
        'views/menu.xml',
    ],

#    'depends': ['queue_job', 'partner_firstname', 'base_location', 'stock_product_location', 'sale_stock', 'product', 'crm', 'stock_account', 'delivery', 'purchase', 'purchase_stock', 'sale_purchase', 'account', 'sales_team', 'delivery', 'helpdesk', 'account_reports', 'mrp'],


    'depends': ['queue_job', 'partner_firstname','base_location', 'sale_stock', 'product', 'crm', 'stock_account', 'delivery', 'purchase', 'purchase_stock', 'sale_purchase', 'account', 'sales_team', 'delivery', 'helpdesk', 'account_reports', 'mrp','stock_product_location'],

    'assets': {
        'web.assets_backend': [
                'price_paper/static/src/js/form_renderer.js',
                'price_paper/static/src/js/product_price_lock.js'
            ],
        'web.assets_qweb': [
            'price_paper/static/src/xml/**/*',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
