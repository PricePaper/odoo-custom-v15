odoo.define('portal_enhancements.basic_info', function (require) {
    'use strict';
    var core = require('web.core');
    var phone_validation = /^[(]?(\d{3})[)]?[-\s]?(\d{3})[-\s]?(\d{4})$/;
    
    var _t = core._t;


    const publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    $.blockUI.defaults.css.border = '0';
    $.blockUI.defaults.css["background-color"] = '';
    $.blockUI.defaults.overlayCSS["opacity"] = '0.9';



    publicWidget.registry.BusinessInformation = publicWidget.Widget.extend({
        selector: '.business_information',
        events: {
            'submit form': '_onFromSubmit',
        },
        init: function (parent, options) {
            this._super.apply(this, arguments);
            const currentYear = new Date().getFullYear();
            for (let year = 1900; year <= 2100; year++) {
                $('#year').append(`<option value="${year}">${year}</option>`)
                
            }
            $('#year').select2({
                placeholder: "Select a year",
                allowClear: true
            });
        },
       
        _onFromSubmit: function (ev) {

            var $self = this
            ev.preventDefault();
            var flag = false
            var vat_flag = false
            var phone_val = $("input[name='phone']")
            var vat_val = $("input[name='vat']")
            var vat_validation = /^\d{2}-\d{7}$/;
            

            if (phone_validation.test(phone_val.val())) {
                phone_val.removeClass('is-invalid')
            }
            else {
                phone_val.addClass('is-invalid')
                var flag = true
            }

            if (vat_validation.test(vat_val.val())) {
                vat_val.removeClass('is-invalid')
            }
            else {
                vat_val.addClass('is-invalid')
                var vat_flag = true
            }



            if (!flag && !vat_flag) {
                var data = {};
                var $form = $('form[action="/web/signup_submit"]')
                var formData = new FormData($form[0]);
                var partner_id = false
                var vat_validation = '^\d{2}-\d{7}$';
                formData.forEach(function (value, key) {
                    if (['company_name', 'name', 'fax_number', 'email', 'vat', 'year_established', 'phone', 'street', 'city', 'zip', 'typeofbusiness'].indexOf(key) > -1) {

                        data[key] = value;
                    }

                    if (['established_state', 'country_id', 'state_id'].indexOf(key) > -1) {
                        if (value) {

                            data[key] = parseInt(value);
                        }
                    }

                    if (key == 'partner_id') {
                        partner_id = value
                    }

                })
                var msg = ("We are processing your request, please wait ...");
                $.blockUI({
                    'message': '<h2 class="text-white"><img src="/web/static/img/spin.png" class="fa-pulse"/>' +
                        '    <br />' + msg +
                        '</h2>'
                });
                ajax.jsonRpc('/business/registration', 'call', { 'data': data, 'partner_id': partner_id }).then(function (result) {
                    if (result.status) {
                        $.unblockUI();
                        $('.sale_prompt').modal('show')
                    }
                })
            }
        }

    })






});
