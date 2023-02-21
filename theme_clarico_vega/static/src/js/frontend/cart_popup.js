odoo.define('theme_clarico_vego.cart_popup', function(require) {
    'use strict';

    const publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var core = require('web.core');
//    var websiteSaleCart = new publicWidget.registry.websiteSaleCart();
    var wSaleUtils = require('website_sale.utils');
    var rpc = require('web.rpc')

    var _t = core._t
    var timeout;

    publicWidget.registry.cart_popup = publicWidget.Widget.extend({
        selector: '#wrapwrap',
        init: function () {
            this._super.apply(this, arguments);
        },
        _onClickRemoveItem: function(ev) {
            /* Remove the cart product while click on the remove product icon from cart */
            $(ev.currentTarget).parent().siblings().find('.js_quantity').val(0).trigger('change');
        },
        _onUpdateQuantity: function(ev){
            /* Update the cart quantity and price while change the product quantity from input */
            ev.preventDefault();
            var $link = $(ev.currentTarget);
            var $input = $link.closest('.input-group').find("input");
            var min = parseFloat($input.data("min") || 0);
            var max = parseFloat($input.data("max") || Infinity);
            var previousQty = parseFloat($input.val() || 0, 10);
            var quantity = ($link.has(".fa-minus").length ? -1 : 1) + previousQty;
            var newQty = quantity > min ? (quantity < max ? quantity : max) : min;

            if (newQty !== previousQty) {
                $input.val(newQty).trigger('change');
            }
            return false;
        },
        _onChangeQuantity: function (ev){
            /* Get the updated data while change the cart quantity from cart. */
            var $input = $(ev.currentTarget);
            var self = this;
            $input.data('update_change', false);
            var value = parseInt($input.val() || 0, 10);
            if (isNaN(value)) {
                value = 1;
            }
            var line_id = parseInt($input.data('line-id'), 10);
            rpc.query({
                route: "/shop/cart/update_json",
                params: {
                    line_id: line_id,
                    product_id: parseInt($input.data('product-id'), 10),
                    set_qty: value
                },
            }).then(function (data) {
                $input.data('update_change', false);
                var check_value = parseInt($input.val() || 0, 10);
                if (isNaN(check_value)) {
                    check_value = 1;
                }
                if (value !== check_value) {
                    $input.trigger('change');
                    return;
                }
                if (!data.cart_quantity) {
                    return window.location = '/shop/cart';
                }
                wSaleUtils.updateCartNavBar(data);
                $input.val(data.quantity);
                $('.js_quantity[data-line-id='+line_id+']').val(data.quantity).html(data.quantity);
                $(".popover-header").html(data.quantity);
                $.get("/shop/cart", {
                    type: 'popover',
                }).then(function(data) {
                    $(".mycart-popover .popover-body").html(data);
                    $('.mycart-popover .js_add_cart_json').off('click').on('click',function(ev) {
                        ev.preventDefault();
                        self._onUpdateQuantity(ev)
                    });
                    $(".mycart-popover .js_quantity[data-product-id]").off('change').on('change',function(ev) {
                        ev.preventDefault();
                        self._onChangeQuantity(ev)
                    });
                    $(".mycart-popover .js_delete_product").off('click').on('click',function(ev) {
                        ev.preventDefault();
                        self._onClickRemoveItem(ev)
                    });
                });
            });
        }
    });
    publicWidget.registry.websiteSaleCartLink.include({
        selector: '.o_wsale_my_cart a[href$="/shop/cart"]',
        _onMouseEnter: function (ev) {
            var self = this;
            clearTimeout(timeout);
            var path = window.location.pathname
            $(this.selector).not(ev.currentTarget).popover('hide');
            timeout = setTimeout(function () {
                if (!self.$el.is(':hover') || $('.mycart-popover:visible').length) {
                    return;
                }
                self._popoverRPC = $.get("/shop/cart", {
                    type: 'popover',
                }).then(function (data) {
                    var cartPopup = new publicWidget.registry.cart_popup();
                    self.$el.data("bs.popover").config.content = data;
                    self.$el.popover("show");
                    $(".mycart-popover .popover-body").html(data);
                    if (path == '/shop/payment')
                    {
                        $(".mycart-popover .popover-body").find('.te_prod_rm_info').remove()
                        $(".mycart-popover .popover-body").find('.line_qty').removeClass('d-none')
                        $(".mycart-popover .popover-body").find('.js_delete_product').remove()
                    }
                    $('.popover').on('mouseleave', function () {
                        self.$el.trigger('mouseleave');
                    });
                    $('.mycart-popover .js_add_cart_json').off('click').on('click',function(ev) {
                        ev.preventDefault();
                        cartPopup._onUpdateQuantity(ev)
                    });
                    $(".mycart-popover .js_quantity[data-product-id]").off('change').on('change',function(ev) {
                        ev.preventDefault();
                        cartPopup._onChangeQuantity(ev)
                    });
                    $(".mycart-popover .js_delete_product").off('click').on('click',function(ev) {
                        ev.preventDefault();
                        cartPopup._onClickRemoveItem(ev)
                    });
                    $(".te_clear_cart_popover").on('click', function(ev) {
                        ajax.jsonRpc('/shop/clear_cart', 'call', {}).then(function (data) {
                            location.reload();
                        });
                    });
                });
            }, 300);
        }
    });
    publicWidget.registry.clear_cart = publicWidget.Widget.extend({
        selector: '#wrapwrap',
        read_events: {
            'click .te_clear_cart': '_onClickClearCart',
        },
        _onClickClearCart: function (ev) {
            ev.preventDefault();
            ajax.jsonRpc('/shop/clear_cart', 'call', {}).then(function (data) {
                location.reload();
            });
        },
    });
});
