odoo.define('emipro_theme_base.quick_filter', function(require) {
    'use strict';
    var sAnimations = require('website.content.snippets.animation');
    var publicWidget = require('web.public.widget');
    publicWidget.registry.QuickFilter = publicWidget.Widget.extend({
        selector: ".oe_website_sale",
        events: {
            'click .te_quick_filter_dropdown': 'openQuickFilterPopup',
            'click .te_filter_btn_close': 'closeQuickFilterPopup',
            'click .css_attribute_color': 'hideSidebar',
            'click .te_quick_filter_res': 'openQuickFilterMobile',
        },
        start: function() {
            if ($(window).width() > 991.98) {
                if (!this.isEmpty($('.te_quick_filter_ul'))) {
                    $(".te_quick_filter_dropdown").css("display", "inline-block");
                }
            }
            if ($(window).width() < 991.98) {
                if (this.isEmpty($('.te_quick_filter_ul'))) {
                    $(".te_quick_filter_res").hide();
                }
            }
        },
        openQuickFilterPopup: function(){
            if($('div.te_quick_filter_dropdown_menu').hasClass('is_open'))
            {
                this.closeQuickFilterPopup();
                $('div.te_quick_filter_dropdown_menu').removeClass('is_open');
            }
            else
            {
                $('div.te_quick_filter_dropdown_menu').addClass('is_open');
                /* open quick filter */
                if ($('#products_grid_before').hasClass('sticky-media')) {
                    $('#products_grid_before').css({ position: 'unset', top: 'initial', height: 'auto'});
                    $('#products_grid_before').removeClass('sticky-media');
                }
                $(".te_quick_filter_main_div").toggleClass("active");
                $(".te_quick_filter_dropdown_menu").slideToggle(500);

                $(this).data('clicked', true);
            }
        },
        isEmpty: function(element){
            return !$.trim(element.html())
        },
        hideSidebar: function() {
            /* Close sidebar if filter applies in responsive view */
            if ($(window).width() < 991.98) {
                $('#wrapwrap').removeClass('wrapwrap_trans');
            }
        },
        closeQuickFilterPopup: function(){
            $('div.te_quick_filter_dropdown_menu').removeClass('is_open');
            /* Close quick filter in responsive view */
            $('.te_quick_filter_dropdown_menu').slideUp();
            $(".te_quick_filter_dropdown_menu").removeClass("te_open");
        },
        openQuickFilterMobile: function(){
            /* open quick filter in responsive view */
            if ($(window).width() < 991.98) {
                $(".te_quick_filter_dropdown_menu").addClass("te_open");
                $(".te_quick_filter_dropdown_menu").show();
                $("#products_grid_before").scrollTop(0);
                $("#wsale_products_attributes_collapse").addClass("show");

            }
        }
    });

    $(document).mouseup(function(e) {
        var container = $(".te_quick_filter_dropdown_menu");
        /* hide quick filter if click outside the popup */
        if(e.target.className != "te_quick_filter_dropdown btn btn-sm te_sort_btn align-middle") {
            if (!container.is(e.target) && container.has(e.target).length === 0) {
                $(".te_quick_filter_main_div").removeClass('active');
                container.slideUp();
            }
        }
    });

    $(document).keyup(function(e) {
        /* hide quick filter if Escape key press */
        if (e.key === "Escape") {
            $(".te_quick_filter_main_div").removeClass('active');
            $('.te_quick_filter_dropdown_menu').slideUp();
        }
    });

});
