# -*- coding: utf-8 -*-

{
    'name': "Odoo fbprophet",

    'summary': """
        Odoo fbprophet integration""",

    'description': """
        This Bridge module interfaces Odoo with forecasting capabilities based on 
        the facebook developed python package fbprophet.
    """,

    'author': 'Confianz Global',
    'website': 'http://confianzit.com',

    'category': 'Other',
    'version': '0.1',
    'license': 'LGPL-3',
    'depends': ['base'],

    'external_dependencies': {
        'python': ['pandas','prophet'],
    },

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
                            #'views/templates.xml',
    ],

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
