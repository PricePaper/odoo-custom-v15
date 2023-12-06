odoo.define('emipro_theme_base.quick_view', function(require) {
    'use strict';

    var sAnimations = require('website.content.snippets.animation');
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var WebsiteSale = publicWidget.registry.WebsiteSale;
    var productDetail = new publicWidget.registry.productDetail();
    var core = require('web.core');
    var QWeb = core.qweb;
    var xml_load = ajax.loadXML(
        '/website_sale_stock/static/src/xml/website_sale_stock_product_availability.xml',
        QWeb
    );
    var Dialog = require('web.Dialog');
    var _t = core._t;


    publicWidget.registry.quickView = publicWidget.Widget.extend({
        selector: "#wrapwrap",
        events: {
            'click .quick-view-a': 'initQuickView',
        },
        initQuickView: function(ev) {
            /* This method is called while click on the quick view icon
             and show the model and quick view data */
            ev.preventDefault()
            self = this;
            var element = ev.currentTarget;
            var product_id = $(element).attr('data-id');
            ajax.jsonRpc('/quick_view_item_data', 'call',{'product_id':product_id}).then(function(data) {
                if($("#wrap").hasClass('js_sale'))
                {
                    $("#quick_view_model_shop .modal-body").html(data);
                    $("#quick_view_model_shop").modal({keyboard: true});
                }else {
                    $("#quick_view_model .modal-body").html(data);
                    $("#quick_view_model").modal({keyboard: true});
                }
                var WebsiteSale = new publicWidget.registry.WebsiteSale();
                if($('#id_lazyload').length) {
                    $("img.lazyload").lazyload();
                }
                WebsiteSale.init();
                WebsiteSale._startZoom();
                var combination = [];
                xml_load.then(function () {
                    var $message = $(QWeb.render(
                        'website_sale_stock.product_availability',
                        combination
                    ));
                    $('div.availability_messages').html($message);
                });

                setTimeout(function(){
                    productDetail.productGallery();
                    $('#mainSlider .owl-carousel').trigger('refresh.owl.carousel');
                    $('#thumbnailSlider .owl-carousel').trigger('refresh.owl.carousel');
                    var quantity = $('.quick_view_content').find('.quantity').val();
                    $('.quick_view_content').find('.quantity').val(quantity).trigger('change');

                }, 200);
                setTimeout(function(){
                    if($(this).find('.a-submit').hasClass('out_of_stock')) {
                        $(this).find('.a-submit').addClass('disabled');
                    }
                }, 1000);
                $('.variant_attribute  .list-inline-item').find('.active').parent().addClass('active_li');
                $( ".list-inline-item .css_attribute_color" ).change(function(ev) {
                    var $parent = $(ev.target).closest('.js_product');
                    $parent.find('.css_attribute_color').parent('.list-inline-item').removeClass("active_li");
                    $parent.find('.css_attribute_color').filter(':has(input:checked)').parent('.list-inline-item').addClass("active_li");
                });

                /*$( ".list-inline-item .css_attribute_color" ).change(function() {
                    $('.list-inline-item').removeClass('active_li');
                    $(this).parent('.list-inline-item').addClass('active_li');
                });*/

                /* Attribute value tooltip */
                $(function () {
                  $('[data-toggle="tooltip"]').tooltip({ animation:true, delay: {show: 300, hide: 100} })
                });

            });

        },
    });
    $('#quick_view_model_shop').on('hidden.bs.modal', function (e) {
        $("#quick_view_model_shop .modal-body").html('');
    });
    $('#quick_view_model').on('hidden.bs.modal', function (e) {
        $("#quick_view_model .modal-body").html('');
    })
    publicWidget.registry.reorder = publicWidget.Widget.extend({
        selector: ".o_portal_my_doc_table, #portal_sale_content",
        events: {
            'click .btn_reorder': 'reorderSale',
        },
        reorderSale: function(ev) {
            /* This method is called while click on the reorder button
             and show the confirm box if stock is not available for any product */
            ev.preventDefault()
            self = this;
            var re_order = $(".o_portal_my_doc_table");
            var $msg = _t("Some Products you want to add in your cart do not have enough stock or they are temporary out of stock ! Do you want to continue ?")
            var $title = re_order.find(".text_reorder").text()
            var element = ev.currentTarget;
            var order_id = $(element).attr('data-id');
            ajax.jsonRpc('/order_check_reorder', 'call', {'order_id':order_id}).then(function(response) {
                if(response)
                {
                    Dialog.confirm(self, $msg,
                    {
                        size: 'medium',
                        title: $title,
                        buttons: [{
                            text: _t('Yes'),
                            classes: 'btn btn-primary yes',
                            close: true,
                            click: function () {
                                ajax.jsonRpc('/order_reorder', 'call',{'order_id':order_id}).then(function(response) {
                                    window.location.href = '/shop/cart';
                                });
                            }
                        }, {
                            text: _t('No'),
                            classes: 'btn btn-secondary no',
                            close: true,
                        }]
                    });
                }
                else {
                    ajax.jsonRpc('/order_reorder', 'call',{'order_id':order_id}).then(function(response) {
                                    window.location.href = '/shop/cart';
                                });
                }
            });
            },
        });
});
