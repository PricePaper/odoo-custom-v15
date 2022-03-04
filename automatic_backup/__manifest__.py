# -*- coding: utf-8 -*-
{
    'name': 'Automatic Backup (Dropbox, Google Drive, Amazon S3, SFTP)',
    'version': '15.0.0',
    'summary': 'Automatic Backup',
    'author': 'Grzegorz Krukar (grzegorzgk1@gmail.com)',
    'description': """
    Automatic Backup
    """,
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/automatic_backup.xml',
        'security/security.xml'
    ],
    'depends': [
        'mail',
    ],
    'assets': {
        'web.assets_backend': [
            'automatic_backup/static/src/js/automatic_backup.js',
        ],
        'web.assets_qweb': [
        ],
    },
    'installable': True,
    'application': True,
    'price': 30.00,
    'currency': 'EUR',
}
