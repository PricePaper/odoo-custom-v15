

{
    'name': 'Uom Extension',
    'version': '1',
    'summary': 'Uom Extension',
    'description': """
Uom Extension
=======================
Modifying default uom
    """,
    'author': 'Confianz Global',
    'depends': ['product','price_paper', 'batch_delivery', 'stock_available_unreserved','price_paper', 'purchase', 'stock',
                'stock_orderpoint_enhancements', 'purchase_stock', 'delivery', 'purchase_reception_notify'],
    'sequence': 1600,
    'demo': [
    ],
    'data': [
    'security/ir.model.access.csv',
    'views/product_view.xml',
    'views/stock_quant_view.xml',
    'views/change_product_uom.xml',
    'views/stock_orderpoint_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
