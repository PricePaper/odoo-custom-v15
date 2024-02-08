# -*- coding: utf-8 -*-
{
    # Theme information
    'name': 'Emipro Theme Base',
    'category': 'Base',
    'summary': 'Base module containing common libraries for all Emipro eCommerce themes.',
    'version': '4.1.4',
    'license': 'OPL-1',
    'depends': [
        'website_sale_wishlist',
        'website_sale_comparison',
        'website_blog',
    ],

    'data': [
        'data/slider_styles_data.xml',
        'views/synonym_group_views.xml',
        'security/ir.model.access.csv',
        'templates/template.xml',
        'templates/product_snippet_popup.xml',
        'templates/brand_category_snippet_popup.xml',
        'templates/pwa.xml',
        'templates/assets.xml',
        'views/res_config_settings.xml',
        'views/product_template.xml',
        'views/product_attribute_value_view.xml',
        'views/product_public_category.xml',
        'views/product_brand_ept.xml',
        'views/website_menu_view.xml',
        'views/slider_filter.xml',
        'views/product_label.xml',
        'views/product_tabs.xml',
        'views/ir_attachment.xml',
        'wizard/product_document_config.xml',
        'views/menu_label.xml',
        'wizard/product_brand_wizard_view.xml',
        'templates/image_hotspot_popup.xml',
        'templates/offilne.xml',
        'templates/product_variants.xml',
        'views/search_keyword_report_views.xml',
        'views/website.xml',
    ],
    # 'qweb': ['static/src/xml/advanced_search.xml'],
    'assets': {
        'web.assets_frontend': [
            'emipro_theme_base/static/src/scss/product_slider_editor.scss',
            'emipro_theme_base/static/src/scss/image_hotspot_editor.scss',
            'emipro_theme_base/static/src/js/frontend/category_brand_slider.js',
            'emipro_theme_base/static/src/js/frontend/image_hotspot_events.js',
            'emipro_theme_base/static/src/js/frontend/lazy_load.js',
            'emipro_theme_base/static/src/js/frontend/load_more.js',
            'emipro_theme_base/static/src/js/frontend/product_slider.js',
            'emipro_theme_base/static/src/js/frontend/product_offer_timer.js',
            'emipro_theme_base/static/src/js/frontend/quick_filter.js',
            'emipro_theme_base/static/src/js/frontend/pwa_web.js',
            'emipro_theme_base/static/src/js/frontend/ajax_color_pane.js',
            'emipro_theme_base/static/src/js/frontend/slider_color_pane.js',
        ],
        'website.assets_editor': [
            'emipro_theme_base/static/src/js/snippet/slider_builder_common_editor.js',
            'emipro_theme_base/static/src/js/snippet/category_brand_editor.js',
            'emipro_theme_base/static/src/js/snippet/image_hotspot_snippet.js',
            'emipro_theme_base/static/src/js/menu/category_content_editor.js',
            'emipro_theme_base/static/src/js/snippet/product_builder_editor.js',
            'emipro_theme_base/static/src/js/snippet/slider_builder_helper.js',
        ],
        'web_editor.assets_wysiwyg': [
            'emipro_theme_base/static/src/js/wysiwyg/widgets/dynamic_category_wysiwyg.js',
            'emipro_theme_base/static/lib/odoo-editor/src/OdooEditor.js',
        ],
    },
    # Odoo Store Specific
    'images': [
        'static/description/emipro_theme_base.jpg',
    ],

    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'https://www.emiprotechnologies.com',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',

    # Technical
    'installable': True,
    'auto_install': False,
    'price': 19.00,
    'currency': 'EUR',
}
