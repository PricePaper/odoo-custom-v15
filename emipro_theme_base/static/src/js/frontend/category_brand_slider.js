//----------------------------------------------------
// Dynamic Brand Category Slider Snippet
//----------------------------------------------------
odoo.define('website_category_brand_slider.front_js', function(require) {
    'use strict';
    var publicWidget = require('web.public.widget');
    var ajax = require("web.ajax");
    var OwlMixin = require('theme_clarico_vega.mixins');
    publicWidget.registry.js_category_brand_snippet = publicWidget.Widget.extend(OwlMixin, {
        selector: '.js_category_brand_snippet',
        start: function() {
            this.redrow();
        },
        stop: function() {
            this.clean();
        },
        redrow: function(debug) {
            this.clean(debug);
            this.build(debug);
        },
        destroy: function() {
            this.$el.find('.slider_body').toggleClass('d-none', true);
            this.$el.find('.slider_edit_msg').toggleClass('d-none', false);
            this._clearContent();
            this._super.apply(this, arguments);
        },
        _clearContent: function() {
            const $dynamicSnippetTemplate = this.$el.find('.slider_body');
            if ($dynamicSnippetTemplate) {
                $dynamicSnippetTemplate.html('');
            }
        },
        clean: function(debug) {
            this.$target.empty();
        },
        build: function(debug) {
            var self = this;
            var item_ids = self.$target.attr("data-item_ids");
            var name = self.$target.attr("name");
            var style = self.$target.attr('data-style')
            var sort_by = self.$target.attr('data-sort_by')
            var limit = self.$target.attr('data-limit')
            var product_count = self.$target.attr('data-product_count')

            var params = {
                'name': name,
                'style': style,
                'item_ids': item_ids,
                'sort_by': sort_by,
                'limit': limit,
                'product_count': product_count,
            }
            // Render the category and brand slider
            this.$relativeTarget = $('#wrapwrap'); // #wrapwrap for now bcoz window is not scrolleble in v14
            var position = this.$relativeTarget.scrollTop();
            this.$sticky = self.$target;
            var elementTop = self.$sticky.offset().top;
            var elementBottom = elementTop + self.$sticky.outerHeight();
            var windowHeight = window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight;
            if (elementTop < windowHeight && elementTop != 0) {
                self.ajaxCall(self, params)
            } else {
                this.$relativeTarget.on('scroll.snippet_root_scroll', _.throttle(ev => {
                    var viewportTop = $('#wrapwrap').scrollTop();
                    var viewportBottom = viewportTop + $('#wrapwrap').height();
                    if (elementBottom > position && elementTop < viewportBottom) {
                        self.ajaxCall(self, params)
                        position = scroll;
                    }
                }, 200));
            }
        },
        ajaxCall: function(self, params) {
            ajax.jsonRpc('/slider/category-brand-render', 'call', params).then(function(data) {
                $(self.$target).html(data);
                if ($('#id_lazyload').length) {
                    $("img.lazyload").lazyload();
                }
                self.initOwlSlider();
            })
        },
        initOwlSlider: function() {
            $('.brand_slider_template_3 .brand_carousel').each(function(index) {
                var $items = $(this);
                var items = $items.find(".item").length,
                loop = items > 3 ? true : false,
                responsive = { 0: {items: 2, loop: items > 2 ? true : false}, 576: {items: 3, loop: loop}, 992: {items: 2, loop: items > 2 ? true : false}, 1300: {items: 3, loop: loop} };
                OwlMixin.initOwlCarousel('.brand_slider_template_3 .brand_carousel', 10, responsive, loop, 3, false, true, false, false, false, false, true, false);
            })
            $('.category_carousel, .brand_carousel').each(function(index) {
                var $items = $(this);
                var items = $items.find(".item").length,
                loop = items > 6 ? true : false,
                responsive = { 0: {items: 2, loop: items > 2 ? true : false}, 576: {items: 3, loop: items > 3 ? true : false}, 991: {items: 4, loop: items > 4 ? true : false}, 1200: {items: 6, loop: loop} };
                OwlMixin.initOwlCarousel('.category_carousel, .brand_carousel', 10, responsive, loop, 6, false, true, false, false, false, false, true, false);
            })
        },
    });
})
