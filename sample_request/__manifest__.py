{
    'name': 'Sample Request',
    'version': '1.0',
    'category': 'sale',
    'license': 'AGPL-3',
    'description': """
This is a module allows users to request the sample 
of products and admin have rights to approve to reject them
==============================================
""",
    'author': 'Confianz Global,Inc.',
    'website': 'https://www.confianzit.com',
    'depends': ['website_sale'],
    'data': [  
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/res_config.xml',
        'views/templates.xml',
        'views/sample_request.xml'
    ],
    'demo': [  ],
    'assets': {
        'web.assets_frontend': [
            'sample_request/static/src/js/main.js',
            'sample_request/static/src/scss/main.scss',
        ]
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'images': [],
}
