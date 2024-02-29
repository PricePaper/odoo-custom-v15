odoo.define('portal_enhancements.common', function (require) {
    'use strict';
    var core = require('web.core');
    const publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    $.blockUI.defaults.css.border = '0';
    $.blockUI.defaults.css["background-color"] = '';
    $.blockUI.defaults.overlayCSS["opacity"] = '0.9';



    publicWidget.registry.NewManager = publicWidget.Widget.extend({
        selector: '.new_manager',
        events: {
            'click .new_manager': '_createNewManager'
        },
        _createNewManager: function (ev) {
            var name = $("#contactName").val()
            var email = $("#contactEmail").val()
            var phone = $("#contactPhone").val()
            var note = $("#contactNote").val()
            if (!name) {
                $("#contactName").addClass('invalid')
            }
            else if (!email) {
                $("#contactEmail").addClass('invalid')
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
                            comany_access: comany_access

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

