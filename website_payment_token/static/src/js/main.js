odoo.define('website_paymet_token.token', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var _t = core._t;



    publicWidget.registry.paymentToken = publicWidget.Widget.extend({
        selector: '#generateModal',
        events: {
            'click .token_generate': '_genrateToken',
            'change #deliveryaddress': "_deliveryToggle"

        },
        _deliveryToggle: function (ev) {
            if ($(ev.currentTarget).is(":checked")) {
                $('.delivey_select').removeClass('d-none');
            }
            else {
                $('.delivey_select').addClass('d-none');
            }
        },
        _genrateToken: function (ev) {

            var card_num = $("input[name=card_num]").val()
            var flag = false
            if (!card_num) {
                $("input[name=card_num]").addClass('is-invalid')
                $("input[name=card_num]").get(0).setCustomValidity('Please Enter Correct Card Number');
                $("input[name=card_num]").get(0).reportValidity()
                flag = true
            }
            var expiry_month = $("#cardMonth").val()
            if (!expiry_month) {
                $("#cardMonth").addClass('is-invalid')
                $("input[name=card_num]").get(0).setCustomValidity('Please Enter Correct Month');
                $("input[name=card_num]").get(0).reportValidity()
                
                flag = true
            }
            var expiry_year = $("#cardYear").val()
            if (!expiry_year) {
                $("#cardYear").addClass('is-invalid')
                $("cardYear").get(0).setCustomValidity('Please Enter Correct Year');
                $("cardYear").get(0).reportValidity()
                flag = true
            }
            var card_cvv = $("input[name='card_cvv']").val()
            if (!card_cvv) {
                $("input[name=card_cvv]").addClass('is-invalid')
                $("input[name=card_cvv]").get(0).setCustomValidity('Please Enter Correct Cvv');
                $("input[name=card_cvv]").get(0).reportValidity()
                flag = true
            }
            if (!flag) {
                this._rpc({
                    route: '/my/generate/token',
                    params: {
                        is_delivery: $("input[name=delivery_address]").is(":checked"),
                        partner_shipping_id: $('#delivery').val(),
                        is_default: $("input[name=default_token]").is(":checked"),
                        partner_id: $('#billing').val(),
                        exp_month: $("#cardMonth").val(),
                        card_code: $("input[name='card_cvv']").val(),
                        card_no: $("input[name=card_num]").val(),
                        exp_year: $("#cardYear").val()
                    }
                }).then(function (res) {
                    window.location.reload()
                })
            }
        }
    })
})