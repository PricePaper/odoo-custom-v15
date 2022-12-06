# -*- coding: utf-8 -*-

{
    "name": "Scan barcode and QR code using mobile camera and webcam | Barcode and QR code scanner widget for many2one and character field | Search any document by barcode and QR code globally using search view",
    "version":"15.0.2",
    "license": "OPL-1",
    "support": "relief.4technologies@gmail.com",  
    "author" : "Relief Technologies",    
    "category": "Extra Tools",
    "summary": "All in one mobile barcode QR code scanner barcode and qr code scanner widget mobile barcode mobile qr code mobile qrcode barcode scanner qr code scanner mobile qrcode scanner mobile barcode scanner mobile qrcode scanner",
    "description": """

    """,
    "depends": [
    "base",
    "web",
    ],
    "data": [],    
    'assets': {
        'web.assets_backend': [
            'rt_widget_qr_cam/static/src/scss/qr_field_backend.scss',
            'rt_widget_qr_cam/static/src/js/jsQR.js',
            'rt_widget_qr_cam/static/src/js/quagga.min.js',
            'rt_widget_qr_cam/static/src/js/qr_field_backend.js',   
            'rt_widget_qr_cam/static/src/js/rt_qr_searchbar.js',             
                                 
        ],
        'web.assets_qweb': [
            'rt_widget_qr_cam/static/src/xml/**/*',
        ],
    },     
     
    "images": ["static/description/background.png",],              
    "installable": True,
    "application": True,
    "auto_install": False,
    "price": 60,
    "currency": "EUR"   
}
