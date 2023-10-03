# -*- coding: utf-8 -*-

{
    'name': 'Purchase Extension',
    'version': '1.0',
    'license': 'LGPL-3',
    'category': 'Purchase',
    'summary': "Purchase",
    'description': """
Custom module implemented for Purchase extension.
       """,
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',
    'data': [
        'security/price_paper_security.xml',
        'data/mail_template.xml',
        'views/account_vendor_bill.xml',
        'views/product_view.xml',
        'views/product_pricelist.xml',
        'security/ir.model.access.csv',
        'views/purchase_order.xml',
        'views/purchase_order_line.xml',
        'views/purchase_requisition_views.xml',
        'views/res_company.xml',
        'views/res_partner.xml',
        'views/sale_order.xml',
        'views/report_pdf_vendor_product.xml',
        'views/report_template.xml',
        'views/purchase_report_template.xml',
        'wizard/view_sale_history_po_views.xml',
        'wizard/cost_discrepancy_report_template.xml',
        'wizard/vendor_product_report_wizard.xml',
        'wizard/update_vendor_pricelist_view.xml',
        'wizard/add_sales_history_to_po.xml',
        'wizard/change_product_uom.xml',
        'wizard/update_unit_price.xml',
    ],
    'depends': ['purchase_requisition', 'stock_orderpoint_enhancements'],
    'assets': {
        'web.assets_backend': ['/purchase_extension/static/src/js/action_manager.js'],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
