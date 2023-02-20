odoo.define('theme_clarico_vega.slider_color_pane_process', function (require) {

    "use strict";
    var publicWidget = require('web.public.widget')
    var ajax = require('web.ajax')
    var core = require('web.core');
    var wSaleUtils = require('website_sale.utils');
    var _t = core._t;

    publicWidget.registry.SliderColorPane = publicWidget.Widget.extend({
        selector: '#wrapwrap',
        read_events: {
            'mouseenter .te_cv_slider': '_onMouseEnterColorHoverInSlider',
            'mouseleave .te_cv_slider': '_onMouseEnterColorHoverOutSlider',
        },
        _onMouseEnterColorHoverInSlider: function(ev) {
            const $target = $(ev.currentTarget);
            var self = this;
            var color_id = $target.attr('data-variant-color')
            var product_id = $target.attr('data-product-id')
            var params = {
                'color_id': color_id,
                'product_id': product_id,
                'hover': true,
            }
            ajax.jsonRpc('/hover/color', 'call', params).then(function (data){
                $target.parents('form').find('.o_carousel_product_card_img_top').attr('src', data);
            });
        },
        _onMouseEnterColorHoverOutSlider: function(ev) {
            const $target = $(ev.currentTarget);
            var self = this;
            var color_id = $target.attr('data-variant-color')
            var product_id = $target.attr('data-product-id')
            var params = {
                'color_id': color_id,
                'product_id': product_id,
                'hover': false,
            }
            ajax.jsonRpc('/hover/color', 'call', params).then(function (data){
                $target.parents('form').find('.o_carousel_product_card_img_top').attr('src', data);
            });
        },

    });

});
