# -*- coding: utf-8 -*-

{
    'name': 'Price Maintanace',
    'version': '1.0',
    'license': 'LGPL-3',
    'category': 'Sales and Purchase',
    'summary': "Sales and Purchase",
    'description': """
Custom module implemented for Price maintanance.
       """,
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',
    'images': [],

    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'report/cost_change_report_template.xml',
        'views/report_template.xml',
        'data/mail_template.xml',
        'wizard/price_edit_note.xml',
        'views/report_pricelist.xml',
        'views/price_edit_notes.xml',
        'views/res_company.xml',
        'views/res_config_settings.xml',
        'views/product.xml',
        'views/customer.xml',
        'views/customer_product_price.xml',
    ],
    'assets': {
        'web.assets_backend': [
                '/price_maintanance/static/src/js/one2manySearch.js',
            ],
        'web.assets_qweb': [
        ],
    },
    'depends': ['price_paper', 'website_scraping', 'crm_enhancements', 'base_address_city'],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
