# -*- coding: utf-8 -*-
{
    'name': 'Attachment Extension',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'summary': 'Attachment Extension',
    'description': """
    Attachment Extension
    """,
    'author': 'Confianz Global',
    'website': 'http://confianzit.com',
    'depends' : ['base'],

    'data': [
        'security/ir.model.access.csv',
        'views/ir_attachment_tags.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
