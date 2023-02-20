odoo.define('theme_clarico_vega.ajax_color_pane_process', function (require) {

    "use strict";
    var publicWidget = require('web.public.widget')
    var ajax = require('web.ajax')
    var core = require('web.core');
    require('website_sale.website_sale');
    var wSaleUtils = require('website_sale.utils');
    var _t = core._t;


    publicWidget.registry.AjaxColorPane = publicWidget.Widget.extend({
        selector: '.color-changer',
        read_events: {
            'mouseenter .te_cv_sp': '_onMouseEnterColorHover',
            'mouseleave .te_cv_sp': '_onMouseEnterColorHoverOut',
        },
        start: function(ev){
            /* Applied scroll based on the label length */
            var getAttrLabel =  $(this.$el);
            if ($(window).width() < 767 ) {
                if( $(getAttrLabel).find('label').length >= 6 ) {
                    this._attrColorPane(getAttrLabel);
                }
            }
            else if ($(window).width() < 1500 ) {
                if( $(getAttrLabel).find('label').length >= 9 ) {
                    this._attrColorPane(getAttrLabel);
                }
            }
            else {
                if( $(getAttrLabel).find('label').length >= 12 ) {
                    this._attrColorPane(getAttrLabel);
                }
            }
        },
        _attrColorPane: function(getAttrLabel) {
            $(getAttrLabel).mCustomScrollbar({
                   axis:"x",
                   theme:"dark-thin",
                   setWidth: '100%',
                   alwaysShowScrollbar: 0,
                   autoHideScrollbar: true,
            });
        },
        _onMouseEnterColorHover: function(ev) {
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
                $target.parents('.o_wsale_product_grid_wrapper').find('.oe_product_image img').attr('src', data);
            });
        },
        _onMouseEnterColorHoverOut: function(ev) {
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
                $target.parents('.o_wsale_product_grid_wrapper').find('.oe_product_image img').attr('src', data);
            });
        }
    });

});
