odoo.define('emipro_theme_base.load_product_through_ajax', function(require) {
    'use strict';

    const publicWidget = require('web.public.widget');
    require('website_sale.website_sale');
    var ajax = require('web.ajax');
    var config = require('web.config');
    var VariantMixin = require('sale.VariantMixin');
    var ThemeEvent = new publicWidget.registry.ThemeEvent();
    var StickyFilter = new publicWidget.registry.StickyFilter();
    var productDetail = new publicWidget.registry.productDetail();
    var priceSlider = new publicWidget.registry.price_slider();
    var AjaxColorPaneAttr = new publicWidget.registry.AjaxColorPane();
    var quickFilter = new publicWidget.registry.QuickFilter;
    var ProductCategoriesLinks = new publicWidget.registry.ProductCategoriesLinks;
    var core = require('web.core');
    var _t = core._t;

    publicWidget.registry.WebsiteSale.include({
        _changeAttribute: function(event) {
            this._super.apply(this, arguments);
        },
        _onChangeAttribute: function(event) {
            /* This function is inherit for check the filter is through ajax or page load
             And If user change the input of price slider then it's stop this action */
            var target = event.currentTarget;
            if ($(target).hasClass('sliderValue')) {
                event.preventDefault();
                return false;
            }
            var loadAjax = new publicWidget.registry.load_ajax();
            if (!event.isDefaultPrevented()) {
                event.preventDefault();
                loadAjax.filterData(event);
            }
        },
        _startZoom: function() {

            // Do not activate image zoom for mobile devices, since it might prevent users from scrolling the page
            if (!config.device.isMobile) {
                var autoZoom = $('.ecom-zoomable').data('ecom-zoom-auto') || false,
                    attach = '#mainSlider .owl-carousel';
                _.each($('.ecom-zoomable img[data-zoom]'), function(el) {
                    onImageLoaded(el, function() {
                        var $img = $(el);
                        $img.zoomOdoo({
                            event: autoZoom ? 'mouseenter' : 'click',
                            attach: attach
                        });
                        $img.attr('data-zoom', 1);
                    });
                });
            }

            function onImageLoaded(img, callback) {
                $(img).on('load', function() {
                    callback();
                });
                if (img.complete) {
                    callback();
                }
            }
        },
        /*_onClickAdd: function (ev) {
            this._super.apply(this, arguments);
            setTimeout(function(){
                $('.modal').find('footer').find('button').addClass('te_theme_button');
            }, 700);
        },*/
        _updateProductImage: function($productContainer, displayImage, productId, productTemplateId, newCarousel, isCombinationPossible) {
            /* This method is used for update the product images while open a quick view model */
            var $carousel = $productContainer.find('#mainSlider');
            var $thumb_carousel = $productContainer.find('#thumbnailSlider');
            if (window.location.search.indexOf('enable_editor') === -1) {
                var $newCarousel = $(newCarousel);
                $carousel.after($newCarousel);
                $thumb_carousel.after($newCarousel);
                $carousel.remove();
                $thumb_carousel.remove();
                $carousel = $newCarousel;
                this._startZoom();
                productDetail.productGallery();
                $('#mainSlider .owl-carousel').trigger('refresh.owl.carousel');
                $('#thumbnailSlider .owl-carousel').trigger('refresh.owl.carousel');
                // fix issue with carousel height
                this.trigger_up('widgets_start_request', {
                    $target: $carousel
                });
            }
            $carousel.toggleClass('css_not_available', !isCombinationPossible);
            /* update image while update variant */
            var pro_img_src = "/web/image/product.product/" + productId + "/image_128";
            var temp_img_src = "/web/image/product.template/" + productId + "/image_128";
            if ($(".te_ajax_cart_content").length) {
                if ($(pro_img_src.length)) {
                    $(".te_ajax_cart_content").find(".img_section img.variant_image").attr("src", pro_img_src);
                } else {
                    $(".te_ajax_cart_content").find(".img_section img.variant_image").attr("src", temp_img_src);
                }
            }
            $('.css_attribute_color').parents('li').removeClass('active_li')
            $('.css_attribute_color.active').parent('li').addClass('active_li')
            /* Attribute value tooltip */
            $(function() {
                $('[data-toggle="tooltip"]').tooltip({
                    animation: true,
                    delay: {
                        show: 300,
                        hide: 100
                    }
                })
            });
        },
        /**
         * Toggles the add to cart button depending on the possibility of the
         * current combination.
         *
         * @override
         */
        _toggleDisable: function($parent, isCombinationPossible) {
            VariantMixin._toggleDisable.apply(this, arguments);
            $parent.find("#add_to_cart,.quick-add-to-cart").toggleClass('disabled', !isCombinationPossible);
            $parent.find(".o_we_buy_now").toggleClass('disabled', !isCombinationPossible);
        },
        /**
         * Displays SKU and change based on select varient
         * current combination.
         *
         * @override
         */
        _onChangeCombination: function(ev, $parent, combination) {
            this._super.apply(this, arguments);
            $(".js_sku_div").html('N/A');
            if (combination.sku_details) {
                $(".js_sku_div").html(combination.sku_details);
            }
        },
    });

    publicWidget.registry.load_ajax = publicWidget.Widget.extend({
        selector: ".oe_website_sale",
        events: {
            'click .te_clear_attr_a': '_onClearAttribInd',
            'click .te_clear_all_form_selection': '_onClearAttribAll',
            'click .te_clear_all_variant': '_onClearAttribDiv',
        },
        filterData: function(event) {
            /* This method is used to check the load ajax is enable or not
             And If It's enable then send the ajax request otherwise submit the form*/
            var inputMinVal = parseFloat($("input.ept_price_min").val());
            var inputMaxVal = parseFloat($("input.ept_price_max").val());
            var minValue = parseFloat($("#price_slider_min").val());
            var maxValue = parseFloat($("#price_slider_max").val());

            // Don't submit the price filter data if price filter not applied
            if (inputMinVal == minValue && inputMaxVal == maxValue) {
                $("input.ept_price_min").removeAttr('name')
                $("input.ept_price_max").removeAttr('name')
            }
            if ($(".load_products_through_ajax").length) {
                var through_ajax = $(".load_products_through_ajax").val();
                if (through_ajax == 'True') {
                    this.sendAjaxToFilter(event);
                }
            } else {
                $("form.js_attributes input,form.js_attributes select").closest("form").submit();
            }

        },
        sendAjaxToFilter: function(event) {
            /* This method is used foe send the ajax request to get the filtered data */
            $('.cus_theme_loader_layout').removeClass('d-none');
            var url = window.location.pathname;
            var frm = $('.js_attributes')

            var url_prm = frm.serialize()

            url = url + "?" + url_prm;
            window.history.pushState({}, "", url);
            $.ajax({
                url: url,
                type: 'GET',
                success: function(data) {
                    var data_replace = null;
                    data_replace = $(data).find(".o_wsale_products_main_row");
                    $(".o_wsale_products_main_row").replaceWith(data_replace);
                    data_replace = $(data).find('.products_pager:first');
                    $(".products_pager:first").replaceWith(data_replace);
                    data_replace = $(data).find('.products_pager:last');
                    $(".products_pager:last").replaceWith(data_replace);
                    data_replace = $(data).find('.te_shop_filter_resp');
                    $(".te_shop_filter_resp").replaceWith(data_replace);
                    data_replace = $(data).find('.load_more_next_page');
                    $(".load_more_next_page").replaceWith(data_replace);
                    ThemeEvent.onShowClearVariant();
                    ThemeEvent._onslide();
                    $('.products_categories [data-link-href]').click(function(ev) {
                        ProductCategoriesLinks._openLink(ev);
                    });
                    StickyFilter._stickyFilter();
                    priceSlider.start();
                    quickFilter.start();

                    $('.te_cv_sp').mouseenter(function(event) {
                        AjaxColorPaneAttr._onMouseEnterColorHover(event);
                    });
                    $('.te_cv_sp').mouseleave(function(event) {
                        AjaxColorPaneAttr._onMouseEnterColorHoverOut(event);
                    });
                    $("html, body").animate({
                        scrollTop: 0
                    }, 1000);
                    if ($(window).width() < 768) {
                        quickFilter.openQuickFilterPopup();
                        quickFilter.hideSidebar();
                        quickFilter.closeQuickFilterPopup();
                    }

                    $('.nav-item input[type="checkbox"]').click(function() {
                        if ($(this).prop("checked") == false) {
                            var self = $(this);
                            var attr_value;
                            if (self.parent("label").hasClass("css_attribute_color")) {
                                attr_value = self.parent("label").siblings(".te_color-name").html();
                                if (attr_value) {
                                    attr_value = attr_value.toLowerCase();
                                    attr_value = attr_value.replace(/(^\s+|[^a-zA-Z0-9 ]+|\s+$)/g, "");
                                    attr_value = attr_value.replace(/\s+/g, "-");
                                }
                            } else {
                                attr_value = self.siblings("span").html();
                                if (attr_value) {
                                    attr_value = attr_value.toLowerCase();
                                    attr_value = attr_value.replace(/(^\s+|[^a-zA-Z0-9 ]+|\s+$)/g, "");
                                    attr_value = attr_value.replace(/\s+/g, "-");
                                }
                            }
                            if (!attr_value) {
                                attr_value = self.parent("label").hasClass("css_attribute_color") ? self.parent("label").siblings(".te_color-name").html() : self.siblings("span").html();
                            }
                            $('.te_view_all_filter_div .te_view_all_filter_inner').find('.te_clear_attr_a.' + attr_value).trigger('click');
                        }
                    });

                    $("select").change(function() {
                        $(this).find("option:selected").each(function() {
                            var attr_value = $(this).parents('.nav-item').find('.te_clear_all_variant').attr('attribute-name');
                            if (!$(this).text()) {
                                $('.te_view_all_filter_div .te_view_all_filter_inner').find('.te_clear_attr_a.' + attr_value).trigger('click');
                            }
                        });
                    });
                    $('.cus_theme_loader_layout').addClass('d-none');
                    $('#wrapwrap').removeClass('wrapwrap_trans');
                    if ($('#id_lazyload').length) {
                        $("img.lazyload").lazyload();
                    }
                    if($(".color-changer").length) {
                        $(".color-changer").mCustomScrollbar({axis: "x",theme: "dark-thin",alwaysShowScrollbar: 0 });
                    }
                }
            });
        },
        _onClearAttribInd: function(event) {
            /* This method is inherit because check while remove the filtered attribute. And filter to ajax*/
            var self = event.currentTarget;
            var id = $(self).attr("data-id");
            if (id) {
                $("form.js_attributes option:selected[value=" + id + "]").remove();
                $("form.js_attributes").find("input[value=" + id + "]").removeAttr("checked");
            }
            this.filterData(event);
        },
        _onClearAttribAll: function(event) {
            /* This method is inherit because check while remove all the filtered attribute. And filter to ajax*/
            $("form.js_attributes select").val('');
            $("form.js_attributes").find("input:checked").removeAttr("checked");
            this.filterData(event);
        },
        _onClearAttribDiv: function(event) {
            /* This method is inherit to clear attribute div */
            var attr_name = $(event.currentTarget).attr('attribute-name');
            var self = event.currentTarget;
            var curent_div = $(self).parents("li.nav-item");
            var curr_divinput = $(curent_div).find("input:checked");
            var curr_divselect = $(curent_div).find("option:selected");
            _.each(curr_divselect, function(event) {
                $(curr_divselect).remove();
            });
            _.each(curr_divinput, function(event) {
                $(curr_divinput).val('')
            });
            this.filterData(event);
        },
    });
    publicWidget.registry.websiteSaleCategory.include({
        selector: '#wrapwrap .oe_website_sale',
    });
});
