{
    'name' : 'Many2many_tags widget enhancement',
    'version': '15.0',
    'category': 'Productivity/Documents',
    'description': """
        Fix bug for many2many tags widget for many2many fields
       """,
    'author': 'Confianz Global,Inc.',
    'website': 'https://www.confianzit.com',
    'images': [],
    'depends' : ['web'],
    'data': [


    ],
    'assets': {

      'web.assets_backend': [
       'many2many_tags_enahncement/static/src/js/many2many_tags_enhancement.js',
      ],


     },
    'installable': True,
    'application': False,
}
