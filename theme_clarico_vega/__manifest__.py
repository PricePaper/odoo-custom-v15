{
    # Theme information

    'name': 'Theme Clarico Vega',
    'category': 'Theme/eCommerce',
    'summary': 'Our Top selling Theme Clarico Vega is Fully Responsive, Clean, Modern , Sectioned Odoo Theme. '
               'Crafted to be Pixel Perfect , It is suitable for eCommerce Businesses like '
               'Furniture , Fashion , Electronics , Beauty , Health , Fitness , Jewelry , '
               'Sports etc It can handle all the B2B and B2C website related needs of the '
               'customer’s business.Being fully Mobile Responsive, it looks equally '
               'stunning on all kinds of screens and devices. The theme is designed '
               'keeping in mind the delivery of great user experience to your '
               'customers, and also a User friendly interface for the admin to manage '
               'the store flawlessly. Rest assured, The Clarico Vega will make your web '
               'store look stunningly beautiful.Customers can manage multiple websites '
               'or multi company websites or multiple stores from our Clarico vega theme.'
               'Fully Functional Theme, Flexible Theme, Fast Theme, Modern Multipurpose Theme, '
               'Lightweight Theme, Animated Theme, Advance Theme, Customizable Theme, '
               'Multi Tab Theme Odoo, Attractive Theme, Elegant Theme, Community Theme, '
               'Odoo Enterprise Theme, Responsive Web Client, Mobile Theme , Mobile Responsive '
               'for Odoo Community, Ecommerce theme, odoo theme , B2B theme , B2C theme',
    'version': '4.1.5',
    'license': 'OPL-1',
    'depends': [
        # 'website_theme_install',
        'website_sale_stock_wishlist', 'emipro_theme_base'],

    'data': [
        'data/compare_data.xml',
        'templates/emipro_dynamic_snippets.xml',
        'templates/category.xml',
        'templates/compare.xml',
        'templates/assets_pwa.xml',
        'templates/emipro_custom_snippets.xml',
        'templates/odoo_default_snippets.xml',
        'templates/emipro_snippets_settings.xml',
        'templates/odoo_default_buttons_style.xml',
        'templates/theme_customise_option.xml',
        'templates/blog.xml',
        'templates/shop.xml',
        'templates/price_filter.xml',
        'templates/login_popup.xml',
        'templates/header.xml',
        'templates/footer.xml',
        'templates/portal.xml',
        'templates/wishlist.xml',
        'templates/cart.xml',
        'templates/quick_view.xml',
        'templates/product.xml',
        'templates/product_label.xml',
        'templates/ajax_cart.xml',
        'templates/menu_config.xml',
        'templates/404.xml',
        'templates/brand.xml',
        'templates/comingsoon.xml',
        'templates/emipro_dynamic_snippets_styles.xml',
    ],

    'assets': {
        'web._assets_frontend_helpers': [
            'theme_clarico_vega/static/lib/theme/para_size.scss',
            'theme_clarico_vega/static/lib/theme/variables.scss',
            'theme_clarico_vega/static/lib/theme/button.scss',
            'theme_clarico_vega/static/lib/theme/heading_size.scss',
            'theme_clarico_vega/static/lib/theme/link_color.scss',
        ],

        'web._assets_primary_variables': [
            'theme_clarico_vega/static/src/scss/theme_color.scss',
            'theme_clarico_vega/static/src/scss/customise_variables.scss',
        ],

        'website.assets_wysiwyg': [
            'theme_clarico_vega/static/src/js/editor/snippets.editor.js',
        ],
        'web.assets_frontend': [
            "theme_clarico_vega/static/src/scss/mixins.scss",
            "theme_clarico_vega/static/src/scss/snippets.scss",
            "theme_clarico_vega/static/src/scss/blog.scss",
            "theme_clarico_vega/static/src/scss/customise_option.scss",
            "theme_clarico_vega/static/src/scss/layout.scss",
            "theme_clarico_vega/static/src/scss/megamenu.scss",
            "theme_clarico_vega/static/src/scss/portal.scss",
            "theme_clarico_vega/static/src/scss/owl.carousel.min.css",
            "theme_clarico_vega/static/src/scss/ept_apps.scss",
            "theme_clarico_vega/static/src/scss/style_1.scss",
            "theme_clarico_vega/static/src/scss/style_2.scss",
            "theme_clarico_vega/static/src/scss/style_3.scss",
            "theme_clarico_vega/static/src/scss/style_4.scss",
            "theme_clarico_vega/static/src/scss/style_5.scss",
            "theme_clarico_vega/static/src/scss/product_slider.scss",
            "theme_clarico_vega/static/src/scss/label/sale_label.scss",
            "theme_clarico_vega/static/src/scss/snippet_video_popup.scss",
            "theme_clarico_vega/static/src/scss/jquery.mCustomScrollbar.css",
            "theme_clarico_vega/static/src/js/frontend/owl.carousel.js",
            "theme_clarico_vega/static/src/js/frontend/theme_script.js",
            "theme_clarico_vega/static/src/js/frontend/mixins.js",
            "theme_clarico_vega/static/src/js/frontend/login_popup.js",
            "theme_clarico_vega/static/src/js/frontend/multi_item_carousel.js",
            "theme_clarico_vega/static/src/js/frontend/offer_snippent_frontend.js",
            "web/static/lib/jquery.touchSwipe/jquery.touchSwipe.js",
            "theme_clarico_vega/static/src/js/frontend/plugins.js",
            "theme_clarico_vega/static/src/js/frontend/snippet_video_popup.js",
            "emipro_theme_base/static/src/js/frontend/jquery_ui_slider.js",
            "theme_clarico_vega/static/src/js/frontend/cart_popup.js",
            "emipro_theme_base/static/src/js/frontend/quick_view.js",
            "emipro_theme_base/static/src/js/frontend/price_slider.js",
            "emipro_theme_base/static/src/js/frontend/banner_video.js",
            "emipro_theme_base/static/src/js/frontend/load_product_through_ajax.js",
            "theme_clarico_vega/static/src/js/frontend/wishlist_animate.js",
            "theme_clarico_vega/static/src/js/frontend/dropdown_animate.js",
            "theme_clarico_vega/static/src/js/frontend/vertical_menu.js",
            "theme_clarico_vega/static/src/js/frontend/jquery.mCustomScrollbar.js",
            "theme_clarico_vega/static/src/js/frontend/jquery.mixitup.min.js",
            "theme_clarico_vega/static/src/js/frontend/jquery.ui.touch-punch.min.js",
            "theme_clarico_vega/static/src/js/frontend/ajax_cart.js",
            "theme_clarico_vega/static/src/js/frontend/optional_product_ajax_cart.js",
            "theme_clarico_vega/static/lib/drift-zoom/drift.js",
            "theme_clarico_vega/static/src/js/frontend/drift_zoom.js",
            "theme_clarico_vega/static/lib/drift-zoom/drift-basic.css",
            "theme_clarico_vega/static/src/scss/header/style1.scss",
            "theme_clarico_vega/static/src/scss/header/style2.scss",
            "theme_clarico_vega/static/src/scss/header/style3.scss",
            "theme_clarico_vega/static/src/scss/header/style4.scss",
            "theme_clarico_vega/static/src/scss/header/style5.scss",
            "theme_clarico_vega/static/src/scss/header/style6.scss",
            "theme_clarico_vega/static/src/scss/header/style7.scss",
            "theme_clarico_vega/static/src/scss/header/style8.scss",
            "theme_clarico_vega/static/src/scss/header/style9.scss",
            "theme_clarico_vega/static/src/scss/header/style10.scss",
            "theme_clarico_vega/static/src/scss/footer/style1.scss",
            "theme_clarico_vega/static/src/scss/footer/style2.scss",
            "theme_clarico_vega/static/src/scss/footer/style3.scss",
            "theme_clarico_vega/static/src/scss/footer/style4.scss",
            "theme_clarico_vega/static/src/scss/footer/style5.scss",
            "theme_clarico_vega/static/src/scss/footer/style6.scss",
            "theme_clarico_vega/static/src/scss/footer/style7.scss",
            "theme_clarico_vega/static/src/scss/button/style1.scss",
            "theme_clarico_vega/static/src/scss/button/style2.scss",
            "theme_clarico_vega/static/src/scss/button/style3.scss",
            "theme_clarico_vega/static/src/scss/button/style4.scss",
            "theme_clarico_vega/static/src/scss/button/style5.scss",
            "theme_clarico_vega/static/src/scss/button/style6.scss",
            "theme_clarico_vega/static/src/scss/button/style7.scss",
            "theme_clarico_vega/static/src/scss/button/style8.scss",
            "theme_clarico_vega/static/src/scss/button/style9.scss",
            "theme_clarico_vega/static/src/scss/button/style10.scss",
            "theme_clarico_vega/static/src/scss/button/style11.scss",
            "theme_clarico_vega/static/src/scss/button/style12.scss",
            "theme_clarico_vega/static/src/scss/button/style13.scss",
            "theme_clarico_vega/static/src/scss/button/style14.scss",
            "theme_clarico_vega/static/src/scss/button/style15.scss",
            "theme_clarico_vega/static/src/scss/button/style16.scss",
            "theme_clarico_vega/static/src/scss/button/style17.scss",
            "theme_clarico_vega/static/src/scss/button/style18.scss",
            ('replace', 'web_editor/static/src/scss/web_editor.frontend.scss',
             'theme_clarico_vega/static/src/scss/web_editor.frontend.scss'),
        ],
        'web.assets_backend': [
            'theme_clarico_vega/static/src/scss/product_variant_backend.scss',
        ],
        'website.assets_editor': [
            'theme_clarico_vega/static/src/js/editor/customise_option.js',
            'theme_clarico_vega/static/src/js/editor/editor.js',
            'theme_clarico_vega/static/src/js/editor/google_map_snippet_backend.js',
        ],

    },

    # Odoo Store Specific
    'live_test_url': 'https://claricovega.theme15demo.emiprotechnologies.com/',
    'images': [
        'static/description/main_poster.jpg',
        'static/description/main_screenshot.gif',
    ],

    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'https://www.emiprotechnologies.com',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',

    # Technical
    'installable': True,
    'auto_install': False,
    'price': 265.00,
    'currency': 'EUR',
}
