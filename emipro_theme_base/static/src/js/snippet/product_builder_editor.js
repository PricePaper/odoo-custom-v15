//--------------------------------------------------------------------------
// Dynamic Category And Brand Slider Builder Editor Configuration
//--------------------------------------------------------------------------
odoo.define('product.slider.editor', function (require) {
'use strict';
    var options = require('web_editor.snippets.options');
    //var publicWidget = require('web.public.widget');
    options.registry.product_list_slider = options.Class.extend({
        // While Editing the slider
        edit_slider : function (){
            this.$target.trigger('click', {'show_popup': true});
        },
        //While Drag and drop the slider
        onBuilt: function () {
            this._super();
            //var saved = this.$target.attr("data-saved") || false;
            if(this.$target.closest('.js_multi_slider').length > 0) {
                return
            }
            this.$target.trigger('click', {'show_popup': true});
        },
    })
});
