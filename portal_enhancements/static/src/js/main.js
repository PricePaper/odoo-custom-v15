odoo.define('portal_enhancements.common', function (require) {
    'use strict';
    var core = require('web.core');
    const publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    $.blockUI.defaults.css.border = '0';
    $.blockUI.defaults.css["background-color"] = '';
    $.blockUI.defaults.overlayCSS["opacity"] = '0.9';

    function validateEmail($email) {
        var emailReg = /^([\w-\.]+@([\w-]+\.)+[\w-]{2,4})?$/;
        return emailReg.test($email);
    }

    publicWidget.registry.NewManager = publicWidget.Widget.extend({
        selector: '.new_manager',
        events: {
            'click .new_manager': '_createNewManager'
        },
        _createNewManager: function (ev) {
            var name = $("#contactName").val()
            var partner_id = $("input[name='partner_id'").val()
            var email = $("#contactEmail").val()
            var phone = $("#contactPhone").val()
            var note = $("#contactNote").val()
            if (!name) {
                $("#contactName").addClass('invalid')
                $("#contactName").get(0).setCustomValidity('Please Enter Name');
                $("#contactName").get(0).reportValidity()
            }
            else if (!email || !validateEmail(email) ) {
                $("#contactEmail").addClass('invalid')
                $("#contactEmail").get(0).setCustomValidity('Please Enter Correct Email');
                $("#contactEmail").get(0).reportValidity()
            }

            else {
                var model_access = []
                var comany_access = []
                $('.model_access:checked').each(function () {
                    model_access.push($(this).val())
                }).promise().done(function () {
                    $('.allowed_company:checked').each(function () {
                        comany_access.push($(this).val())
                    }).promise().done(function () {
                        var msg = ("We are processing your request, please wait ...");
                        $.blockUI({
                            'message': '<h2 class="text-white"><img src="/web/static/img/spin.png" class="fa-pulse"/>' +
                                '    <br />' + msg +
                                '</h2>'
                        });

                        ajax.jsonRpc('/my/manager/create', 'call', {
                            name: name,
                            email: email,
                            phone: phone,
                            note: note,
                            model_access: model_access,
                            comany_access: comany_access,
                            partner_id:partner_id

                        }).then(function (data) {
                            
                            window.location = '/my/managers'
                        })
                    })
                })
            }
        }
    })

    publicWidget.registry.CompanySwithch = publicWidget.Widget.extend({
        selector: '.switch_company_wrap',
        events: {
            'click button.switch_company': '_onCompanySwithch',

        },
        _onCompanySwithch: function (ev) {
            var selected_company = $("select[name='company_switch']").val()
            console.log('hello')
            ajax.jsonRpc('/set/company', 'call', { 'company_id': selected_company }).then(function (result) {
                if (result.status) {
                    if (result.url) {
                        location.replace(result.url)
                    }
                    else {

                        location.replace("/my")
                    }
                }
            })
        }

    })



})

