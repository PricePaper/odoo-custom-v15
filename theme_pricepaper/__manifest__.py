{
    'name': 'Theme Pricepaper',
    'version': '1.0',
    'description': 'Custom theme for pricepaper',
    'summary': 'Theme especially designed for the pricepaper, for managing the ecom',
    'author': 'Confianz Global Pvt. Ltd.',
    'website': 'https://www.confianzit.com/',
    'license': 'LGPL-3',
    'category': 'Theme/eCommerce',
    'depends': [
        'website_sale','website_blog'
    ],
    'data': [
        'views/header/header.xml',
        'views/footer/footer.xml',
        'views/snippet_options.xml',
        'views/snippets/banner.xml',
        'views/snippets/video_banner.xml',
        'views/snippets/good_fit.xml',
        'views/snippets/your_product.xml',
        'views/snippets/price_paper.xml',
        'views/snippets/manufactures.xml',
        'views/snippets/contact_us.xml',
        'views/snippets/use_of_bag.xml',
        'views/aboutus.xml',
        'views/snippets.xml',
        'views/blog.xml'
    ],
    'demo': [
        ''
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_pricepaper/static/src/scss/common.scss',
            'theme_pricepaper/static/src/lib/owl_carosuell/*',
            'theme_pricepaper/static/src/scss/header.scss',
            'theme_pricepaper/static/src/scss/footer.scss',
            'theme_pricepaper/static/src/scss/banner.scss',
            'theme_pricepaper/static/src/scss/about_us.scss',
            'theme_pricepaper/static/src/scss/snippet/*',
            'theme_pricepaper/static/src/js/main.js',
        ],
    },
    'auto_install': False,
    'application': False,
   
   
}

