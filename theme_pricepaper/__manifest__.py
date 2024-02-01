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
        'views/snippets/blog_snippets.xml',
        'views/aboutus.xml',
        'views/snippets.xml',
        'views/blog.xml',
        'views/portal.xml',
        'views/login.xml',
        'views/shop.xml',
        'views/product_page.xml'
    ],
    'demo': [
        ''
    ],
    
    'assets': {
        'web.assets_frontend': [
            # "https://fonts.googleapis.com/css2?family=Poppins:wght@100;200;300;400;500;600;700;800;900&display=swap",
            'https://www.google.com/recaptcha/api.js',
            'theme_pricepaper/static/src/scss/common.scss',
            'theme_pricepaper/static/src/lib/owl_carosuell/*',
            'theme_pricepaper/static/src/js/main.js',
            'theme_pricepaper/static/src/scss/common.scss',
            'theme_pricepaper/static/src/scss/header.scss',
            'theme_pricepaper/static/src/scss/footer.scss',
            'theme_pricepaper/static/src/scss/banner.scss',
            'theme_pricepaper/static/src/scss/about_us.scss',
            'theme_pricepaper/static/src/scss/blog_main.scss',
            'theme_pricepaper/static/src/scss/portal.scss',
            'theme_pricepaper/static/src/scss/shop.scss',
            'theme_pricepaper/static/src/scss/product_page.scss',
            'theme_pricepaper/static/src/scss/snippet/*',
        ],
        'website.assets_editor': [
            'theme_pricepaper/static/src/js/editor.js',
        ],
    },
    'auto_install': False,
    'application': False,
   
   
}
