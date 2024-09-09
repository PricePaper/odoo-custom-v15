{
    'name': 'Website Loyalty Management',
    'description': 'Providing Loyalty Points based on purchases',
    'author': 'Confianz Global',
    'website': '15.0',
    'License': 'LGPL-3',
    'depends': ['website_sale', 'sale','portal','crm_enhancements'],
    'data': ['security/security.xml',
             'security/ir.model.access.csv',
             'wizard/redeem_loyalty_wizard.xml',
             'views/menu.xml',
             'views/loyalty_program.xml',
             'views/res_partner.xml',
             'views/sale_order.xml',
             'views/loyalty_transaction.xml',
             'views/loyalty_tier_config.xml',
             'report/web_loyalty_template.xml',
             'report/website_loyalty_transaction_template.xml',
             'report/website_cart_points.xml',
             'report/website_redeem_payment.xml',] ,
    # 'qweb': [
    #     'static/src/xml/website_sale_templates.xml',
    # ],
    'assets': {
        'web.assets_frontend': [
            'website_loyalty_management/static/src/js/redeem_loyalty.js',
        ],
    },

}
