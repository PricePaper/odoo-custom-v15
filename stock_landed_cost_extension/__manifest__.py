# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'WMS Landed Costs Extension',
    'version': '1',
    'summary': 'Landed Costs Extension',
    'description': """
Landed Costs Management
=======================
This module allows you to easily add extra costs on pickings and decide the split of these costs among their stock moves in order to take them into account in your stock valuation.
    """,
    'depends': ['stock_landed_costs'],
    'category': 'Inventory/Inventory',
    'sequence': 1600,
    'demo': [
    ],
    'data': [
        'views/account_move.xml',
        'views/stock_landed_cost_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
