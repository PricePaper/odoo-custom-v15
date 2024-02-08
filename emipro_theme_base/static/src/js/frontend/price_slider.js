odoo.define('emipro_theme_base.price_slider', function(require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.price_slider = publicWidget.Widget.extend({
        selector: ".oe_website_sale",
        events: {
            'change input.ept_price_min, input.sliderValue, input.ept_price_max':'changeInputVal',
            'click .price_filter_reset':'resetFilter',
            'click #price_slider_filter':'applyFilter',
            'click .price_filter_head':'toggleElement',
        },
        start: function () {
            this.initPriceSlider();
        },
        initPriceSlider: function() {
            /* This method is called for initialize the price slider in at shop page. */
            var searchParams = new URLSearchParams(window.location.search);
            var minValue = parseFloat($("#price_slider_min").val());
            var maxValue = parseFloat($("#price_slider_max").val());
            var urlMinVal = parseFloat(searchParams.get('min_price'));
            var urlMaxVal = parseFloat(searchParams.get('max_price'));
            var inputMinVal = parseFloat($("input.ept_price_min").val());
            var inputMaxVal = parseFloat($("input.ept_price_max").val());
            var showMinVal = minValue || 1;
            var showMaxVal = maxValue || 1;
            if(urlMinVal && urlMaxVal)
            {
                showMinVal = urlMinVal || 1;
                showMaxVal = urlMaxVal || 1;
                $("input.ept_price_min").val(urlMinVal);
                $("input.ept_price_max").val(urlMaxVal);

                $("#ept_price_slider:nth-child(2) .ui-slider-handle").attr("data-content",urlMinVal);
                $("#ept_price_slider:nth-child(3) .ui-slider-handle").attr("data-content",urlMaxVal);
            }
            $("#ept_price_slider").slider({
                range: true,
                step: 1,
                min: minValue || 1,
                max:maxValue || 1,
                values: [showMinVal, showMaxVal],
                slide: function(event, ui) {
                    for (var i = 0; i < ui.values.length; ++i) {
                        $("input.sliderValue[data-index=" + i + "]").val(ui.values[i]);
                        $("#ept_price_slider .ui-slider-handle:nth-child(2)").attr("data-content",ui.values[0]);
                        $("#ept_price_slider .ui-slider-handle:nth-child(3)").attr("data-content",ui.values[1]);
                    }
                }
            });
            if(inputMinVal != minValue || inputMaxVal != maxValue) {
                $(".price_filter_reset").show();
                $(".te_pricerange_content").show();
                $(".price_filter_head").toggleClass("te_fa-minus te_fa-plus")
            }else {
                $(".price_filter_reset").hide();
            }
        },
        changeInputVal: function (event) {
            /* This method is called for set the slider data while change the slider inputs */
            var target = event.currentTarget;
            $("#ept_price_slider").slider("values", $(target).data("index"), $(target).val());
        },
        resetFilter: function (event) {
            /* This method is called for reset the price slider */
            var minValue = parseFloat($("#price_slider_min").val()) || 1;
            var maxValue = parseFloat($("#price_slider_max").val());
            $("input.ept_price_min").val(minValue);
            $("input.ept_price_max").val(maxValue);
            $("#ept_price_slider:nth-child(2) .ui-slider-handle").attr("data-content",minValue);
            $("#ept_price_slider:nth-child(3) .ui-slider-handle").attr("data-content",maxValue);
            $("input.ept_price_min").removeAttr('name')
            $("input.ept_price_max").removeAttr('name')
            $( "#ept_price_slider" ).slider("values",[minValue,maxValue]);
            this.applyFilter();
        },
        applyFilter: function (event) {
            /* This method is called for filter the price data on click the apply filter button */
            var minValue = parseFloat($("#price_slider_min").val());
            var maxValue = parseFloat($("#price_slider_max").val());
            var inputMinVal = parseFloat($("input.ept_price_min").val());
            var inputMaxVal = parseFloat($("input.ept_price_max").val());
            if (inputMinVal == "" || inputMaxVal == "" ||
                isNaN(inputMinVal) || isNaN(inputMaxVal) ||
             inputMinVal < minValue || inputMaxVal > maxValue ||
              inputMinVal > maxValue || inputMaxVal > maxValue ||
               inputMaxVal < minValue || inputMaxVal < inputMinVal) {
                $('.ept_price_slider_error').addClass("price_error_message").html('Invalid Input');
                return false
            }
            var loadThroughAjax = new publicWidget.registry.load_ajax();
            if($(".load_products_through_ajax").length)
            {
                var through_ajax = $(".load_products_through_ajax").val();
                if(through_ajax == 'True')
                {
                    loadThroughAjax.sendAjaxToFilter(event);
                }
            }else {
                $("form.js_attributes input,form.js_attributes select").closest("form").submit();
            }
        },
        toggleElement: function (event) {
            /* This method is called for hide or show the slider element */
            $(".te_pricerange_content").toggle('slow');
            $(".price_filter_head").toggleClass("te_fa-plus te_fa-minus");
        }
    });
});
