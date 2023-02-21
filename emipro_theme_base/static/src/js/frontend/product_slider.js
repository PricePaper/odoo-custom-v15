//----------------------------------------------------
// Dynamic Product Slider Snippet
//----------------------------------------------------
odoo.define('website_slider.front_js', function(require) {
    'use strict';
    var sAnimations = require('website.content.snippets.animation');
    var ajax = require("web.ajax");
    var wSaleUtils = require('website_sale.utils');
    var sale = new sAnimations.registry.WebsiteSale();
    var rpc = require('web.rpc');
    var wish = new sAnimations.registry.ProductWishlist();
    var publicWidget = require('web.public.widget');
    var quickView = require("emipro_theme_base.quick_view");
    var OwlMixin = require('theme_clarico_vega.mixins');
    var quickViewObj = new publicWidget.registry.quickView();

    publicWidget.registry.js_slider_snippet = publicWidget.Widget.extend(OwlMixin, {
        selector: ".js_slider_snippet",
        events: {
            //            'click .product_tabs_main .nav-item a': 'sliderRender',
        },
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
        clean: function(debug) {
            this.$target.empty();
        },
        destroy: function() {
            this.$el.find('.slider_body').toggleClass('d-none', true);
            this.$el.find('.slider_edit_msg').toggleClass('d-none', false);
            this._clearContent();
            this._super.apply(this, arguments);
        },
        _clearContent: function() {
            // Remove the slider html content to speed up while editing the slider
            const $dynamicSnippetTemplate = this.$el.find('.slider_body');
            if ($dynamicSnippetTemplate) {
                $dynamicSnippetTemplate.html('');
            }
        },
        build: function(debug) {
            /* on built snippet render the template of style as per configuration and call the common function
            {Play with Logic} Logic : common method if not given then display first filter data other wise based on
            argument display data on template */
            var self = this;
            var name = self.$target.attr("name");
            var item_ids = self.$target.attr("data-item_ids");
            var discount_policy = self.$target.attr('data-discount_policy')
            var slider_type = self.$target.attr('data-slider_type')
            var style = self.$target.attr('data-style')
            var ui_options = self.$target.attr("data-ui_option");
            var sort_by = self.$target.attr('data-sort_by')
            var limit = self.$target.attr('data-limit')
            var params = {
                'name': name,
                'item_ids': item_ids,
                'slider_type': slider_type,
                'style': style,
                'ui_options': ui_options,
                'limit': limit,
                'sort_by': sort_by,
                'discount_policy': discount_policy,
            }
            // Render the product slider
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
            ajax.jsonRpc('/slider/render', 'call', params).then(function(data) {
                $(self.$target).html(data);
                self.$target.find('.slider_edit_msg').toggleClass('d-none', true);
                if ($('#id_lazyload').length) {
                    $("img.lazyload").lazyload();
                }
                self.initOwlSlider();
                if (!(self.$target.find('.te_pc_style_main').hasClass('ps_style_4_main') || self.$target.find('.owl-carousel').hasClass('te_product_slider_banner'))) {
                    self.$target.find(".slider-color-changer").mCustomScrollbar({axis: "x",theme: "dark-thin",alwaysShowScrollbar: 0 });
                }
                $(self.$target).find(".js_filter_change").first().addClass("active");
                $(self.$target).find(".a-submit").click(function(event) {
                    sale._onClickSubmit(event)
                });
                self.addToWishlist($(self.$target));
                //                self.sliderRender($(self.$target));
                if ($(self.$target).find(".group_website_designer").length == 0) {
                    $(self.$target).removeAttr('data-product_ids data-category_ids data-discount_policy data-ui_option data-name data-limit data-filter_id data-sort_by data-slider_type data-style name data-item_ids')
                }
            });
        },
        addToWishlist: function(target) {
            /* Init wishlist function using wishlist class object also click as per base logic
            base on click disable all data-product-product-id into page */
            var self = this;
            wish.willStart();
            $(target).find(".o_add_wishlist").click(function(event) {
                event.stopImmediatePropagation();
                $(this).prop("disabled", true).addClass('disabled');
                var productId = parseInt($(this).attr('data-product-product-id'), 10);
                $("[data-product-product-id='" + productId + "']").prop("disabled", true).addClass('disabled');
                if (productId && !_.contains(wish.wishlistProductIDs, productId)) {
                    rpc.query({
                        route: '/shop/wishlist/add',
                        params: {
                            product_id: productId,
                        },
                    }).then(function(result) {
                        wish.wishlistProductIDs.push(productId);
                        wish._updateWishlistView();
                        wSaleUtils.animateClone($('#my_wish'), $(this).closest('form'), 25, 40);
                    }).guardedCatch(function(err, data) {
                        $(this).prop("disabled", false).removeClass('disabled');
                        var wproductId = parseInt($(this).attr('data-product-product-id'), 10);
                        $("[data-product-product-id='" + wproductId + "']").prop("disabled", false).removeClass('disabled');
                    });
                    /* Resize menu */
                    setTimeout(() => {
                        $('#top_menu').trigger('resize');
                    }, 200);
                }
            })
        },
        initOwlSlider: function() {
            $('.te_product_slider_1, .te_slider_style_2_right_pannel, .te_product_slider_5, .te_slider_style_6').each(function(index) {
                var $items = $(this);
                var items = $items.find(".item").length,
                mouseDrag = items > 4 ? true : false,
                touchDrag = items > 4 ? true : false,
                pullDrag = items > 4 ? true : false,
                loop = items > 4 ? true : false,
                responsive = { 0: {items: 1, loop: items > 1 ? true : false, mouseDrag: items > 1 ? true : false, touchDrag: items > 1 ? true : false, pullDrag: items > 1 ? true : false}, 576: {items: 2, loop: items > 2 ? true : false, mouseDrag: items > 2 ? true : false, touchDrag: items > 2 ? true : false, pullDrag: items > 2 ? true : false}, 991: {items: 3, loop: items > 3 ? true : false, mouseDrag: items > 3 ? true : false, touchDrag: items > 3 ? true : false, pullDrag: items > 3 ? true : false}, 1200: {items: 4, loop: loop, mouseDrag: mouseDrag, touchDrag: touchDrag, pullDrag: pullDrag} };
                OwlMixin.initOwlCarousel('.te_product_slider_1, .te_slider_style_2_right_pannel, .te_product_slider_5, .te_slider_style_6', 10, responsive, loop, 4, false, true, mouseDrag, touchDrag, pullDrag, false, true, false);
            });
            $('.te_product_slider_4').each(function(index) {
                var $items = $(this);
                var items = $items.find(".item").length,
                loop = items > 2 ? true : false,
                mouseDrag = items > 2 ? true : false,
                touchDrag = items > 2 ? true : false,
                pullDrag = items > 2 ? true : false,
                responsive = { 0: {items: 1, loop: items > 1 ? true : false, mouseDrag: items > 1 ? true : false, touchDrag: items > 1 ? true : false, pullDrag: items > 1 ? true : false}, 576: {items: 2, loop: loop, mouseDrag: mouseDrag, touchDrag: touchDrag, pullDrag: pullDrag} };
                OwlMixin.initOwlCarousel('.te_product_slider_4', 10, responsive, loop, 2, false, true, mouseDrag, touchDrag, pullDrag, false, true, false);
            });
            $('.te_product_slider_banner').each(function(index) {
                var $items = $(this);
                var items = $items.find(".item").length,
                loop = items > 1 ? true : false,
                mouseDrag = items > 1 ? true : false,
                touchDrag = items > 1 ? true : false,
                pullDrag = items > 1 ? true : false,
                responsive = { 0: {items: 1, loop: loop, mouseDrag: mouseDrag, touchDrag: touchDrag, pullDrag: pullDrag}, 500: {items: 2, margin: 20, loop: items > 2 ? true : false, mouseDrag: items > 2 ? true : false, touchDrag: items > 2 ? true : false, pullDrag: items > 2 ? true : false}, 992: {items: 1, loop: loop, mouseDrag: mouseDrag, touchDrag: touchDrag, pullDrag: pullDrag} };
                OwlMixin.initOwlCarousel('.te_product_slider_banner', 10, responsive, loop, 1, true, false, mouseDrag, touchDrag, pullDrag, false, true, false);
            });
            $('.te_slider_style_7, .te_slider_style_8').each(function(index) {
                var $items = $(this);
                var items = $items.find(".product-rows").length,
                mouseDrag = items > 1 ? true : false,
                touchDrag = items > 1 ? true : false,
                pullDrag = items > 1 ? true : false,
                responsive = { 992: {autoplayTimeout: 8000} };
                OwlMixin.initOwlCarousel('.te_slider_style_7, .te_slider_style_8', 10, responsive, true, 1, true, false, mouseDrag, touchDrag, pullDrag, false, true, false);
            });
        },
    });

    publicWidget.registry.js_multi_snippet = publicWidget.Widget.extend({
        selector: ".js_multi_tab_snippet",
        events: {
            'click .product_tabs_main .nav-item a': 'sliderRender',
        },
        sliderRender: function(target) {
            var targetEl = $(target.currentTarget).attr('href') || false;
            var self = this;
            self.$target = $(targetEl).find('.js_slider_snippet')
            var name = self.$target.attr("name");
            var item_ids = self.$target.attr("data-item_ids");
            var discount_policy = self.$target.attr('data-discount_policy')
            var slider_type = self.$target.attr('data-slider_type')
            var style = self.$target.attr('data-style')
            var ui_options = self.$target.attr("data-ui_option");
            var sort_by = self.$target.attr('data-sort_by')
            var limit = self.$target.attr('data-limit')
            var params = {
                'name': name,
                'item_ids': item_ids,
                'slider_type': slider_type,
                'style': style,
                'ui_options': ui_options,
                'limit': limit,
                'sort_by': sort_by,
                'discount_policy': discount_policy,
            }
            if (name) {
                ajax.jsonRpc('/slider/render', 'call', params).then(function(data) {
                    self.$target.html(data);
                    self.$target.find('.slider_edit_msg').toggleClass('d-none', true);
                    if ($('#id_lazyload').length) {
                        $("img.lazyload").lazyload();
                    }
                    var slider_snippet_obj = new publicWidget.registry.js_slider_snippet();
                    slider_snippet_obj.initOwlSlider();
                    if(!self.$target.find('.te_pc_style_main').hasClass('ps_style_4_main') || !self.$target.find('.owl-carousel').hasClass('te_product_slider_banner')) {
                        self.$target.find(".slider-color-changer").mCustomScrollbar({axis: "x",theme: "dark-thin",alwaysShowScrollbar: 0 });
                    }
                    self.$target.find(".js_filter_change").first().addClass("active");
                    self.$target.find(".a-submit").click(function(event) {
                        sale._onClickSubmit(event)
                    });
                    slider_snippet_obj.addToWishlist(self.$target);
                    if (self.$target.find(".group_website_designer").length == 0) {
                        self.$target.removeAttr('data-product_ids data-category_ids data-discount_policy data-ui_option data-name data-limit data-filter_id data-sort_by data-slider_type data-style name data-item_ids')
                    }
                });
            }
        },
    });
    $('.te_product_slider_1.owl-carousel').each(function(index) {
        var responsive = { 0: {items: 1}, 576: {items: 2}, 991: {items: 3}, 1200: {items: 3} };
        OwlMixin.initOwlCarousel('.te_product_slider_1.owl-carousel', 10, responsive, false, 3, false, true, false, false, false, false, true, false);
    });

    $('.js_multi_slider .product_tabs_nav a[data-toggle="tab"]').on('shown.bs.tab', function() {
        var data_id = $(this).attr('aria-controls');
        $('#' + data_id).find('.owl-carousel').trigger('refresh.owl.carousel');
    })
});
