# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Odoo Customization',
    'version': '1.0',
    'category': 'sale',
    'license': 'AGPL-3',
    'description': """
This is a module to fix some the core base things.
And to add some new generic fields
==============================================
""",
    'author': 'Confianz Global,Inc.',
    'website': 'https://www.confianzit.com',
    'depends': ['crm'],
    'data': [  
        'wizard/crm_lead_to_opportunity_views.xml',
      
    ],
    'demo': [  ],
    
    'installable': True,
    'auto_install': False,
    'application': False,
    'images': [],
}
