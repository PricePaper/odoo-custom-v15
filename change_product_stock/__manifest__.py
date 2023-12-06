

{
    'name': 'Change Product Stock',
    'version': '1',
    'summary': 'Change stock of one product to another product',
    'description': """
Change Product Stock
=======================
Change stock of one product to another produc
    """,
    'author': 'Confianz Global',
    'depends': ['uom_extension'],
    'sequence': 1600,
    'demo': [
    ],
    'data': [
    'security/ir.model.access.csv',
    'views/product_view.xml',
    'wizard/change_product_stock.xml'
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
