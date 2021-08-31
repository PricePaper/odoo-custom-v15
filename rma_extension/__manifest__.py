# -*- coding: utf-8 -*-

{
    'name': 'RMA Extension',
    'version': '1.0',
    'category': 'Warehouse',
    'summary': '''Return merchandise authorization
    RMA Return goods
    Exchange goods
    Credit notes
    Replace item
    Goods Return Refund, 
    Exchange, 
    Payback
    ''',
    'description': """
Custom module implemented for RMA for Price Papers.
       """,
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',
    'images': [],

    'depends': ['scs_rma', 'batch_delivery'],
    'data': [
        'wizard/browse_lines_view.xml',
        'views/rma_form_view.xml',
        'views/rma_report_enhancement.xml',
        'views/stock_picking_view.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
