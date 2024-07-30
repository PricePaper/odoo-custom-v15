{
    'name': 'Website Loyalty Management',
    'description': 'Providing Loyalty Points based on purchases',
    'author': 'Confianz Global',
    'website': '15.0',
    'License': 'LGPL-3',
    'depends': ['website_sale', 'sale','portal'],
    'data': ['security/security.xml',
             'security/ir.model.access.csv',
             'views/menu.xml',
             'views/loyalty_program.xml',
             'views/res_partner.xml',
             'views/sale_order.xml',
             'views/loyalty_transaction.xml',
             'views/loyalty_tier_config.xml',
             'report/web_loyalty_template.xml',
             'report/website_loyalty_transaction_template.xml',
             'report/website_cart_points.xml']

}
