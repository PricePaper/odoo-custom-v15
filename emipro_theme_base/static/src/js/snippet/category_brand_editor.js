//--------------------------------------------------------------------------
// Dynamic Category And Brand Slider Builder Editor Configuration
//--------------------------------------------------------------------------
odoo.define('category.brand.slider.editor', function(require) {
    'use strict';
    var options = require('web_editor.snippets.options');
    var publicWidget = require('web.public.widget');
    options.registry.category_brand_slider = options.Class.extend({
        // While Editing the slider
        edit_category_brand_slider: function() {
            this.$target.trigger('click', {
                'show_popup': true
            });
        },
        //While Drag and drop the slider
        onBuilt: function() {
            this._super();
            this.$target.trigger('click', {
                'show_popup': true
            });
        },
    })
});
