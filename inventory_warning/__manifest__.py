# -*- coding: utf-8 -*-

{
    'name': 'Low Inventory Warning',
    'version': '15.0.0.1',
    'license': 'LGPL-3',
    'category': 'Inventory',
    'summary': "Inventory",
    'description': """
Custom module implemented for Price Papers for Raising low inventory warning.
=============================================================================
Creates a helpdesk ticket if a product added in a Sale line is low in inventory.
       """,
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',
    'images': [],

    'data': [
                'views/helpdesk_team_view.xml',
                'data/data.xml',
             ],

    'depends': ['sale', 'helpdesk'],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
