{
    'name': 'Address Book',
    'version': '1.0',
    'category': 'sale',
    'license': 'AGPL-3',
    'description': """
This is a module allows users to manage it's child contacts from the website
==============================================
""",
    'author': 'Confianz Global,Inc.',
    'website': 'https://www.confianzit.com',
    'depends': ['website_sale'],
    'data': [  
        'views/portal_template.xml'
    ],
    'demo': [  ],
    'assets': {
        'web.assets_frontend': [
            'pp_address_book/static/src/js/main.js',
        ]
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'images': [],
}