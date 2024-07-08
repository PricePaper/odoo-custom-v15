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
            else if (!email || !validateEmail(email)) {
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
                            partner_id: partner_id

                        }).then(function (data) {

                            window.location = '/my/managers'
                        })
                    })
                })
            }
        }
    })

    publicWidget.registry.BusinessInformation = publicWidget.Widget.extend({
        selector: '.business_information',
        events: {
            'submit form': '_onFromSubmit',
        },
        _onFromSubmit: function (ev) {

            var $self = this
            ev.preventDefault();
            var data = {};
            var $form = $('form[action="/web/signup_submit"]')
            var formData = new FormData($form[0]);
            var partner_id = false
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


            // $self._rpc({
            //     model: 'res.partner',
            //     method: 'write',
            //     args: [[parseInt(partner_id)], data],

            // }).then(function(){
            //     console.log('compleet')
            // });
        }

    })

    publicWidget.registry.CompanySwithch = publicWidget.Widget.extend({
        selector: '.switch_company_wrap',
        events: {
            'click button.switch_company': '_onCompanySwithch',
            'click .sale_prompt_popup': '_openSalePrompt',
            'click .payment_prompt_popup': '_openPaymentPrompt'

        },
        _openPaymentPrompt: function (ev) {
            $('.payment_prompt').modal('show');
        },
        _openSalePrompt: function (ev) {
            $('.sale_prompt').modal('show');
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

                        location.reload();
                    }
                }
            })
        }

    })


    publicWidget.registry.PaymentPrompt = publicWidget.Widget.extend({
        selector: '.payment_prompt',
        events: {
            'click .close': '_CloseModel',
            // 'change input[name="flexRadioDefault"]': '_taxSelection',
            'click .save_changes': '_saveChanges'
        },
        _saveChanges: function (ev) {
            var payment_value = $('input[name="flexRadioDefault"]:checked').val()
            var data = {}
            var reader = new FileReader();
            var $self = this
            if (!payment_value) {
                $('.error_div').removeClass('d-none')
                $('.error_div').find('.error_mg').text('Kindly Select the payment option.')
            }
            else{
                data = {
                    'payment_value':payment_value
                }
                $self._rpc({
                    route: "/update/business/payment",
                    params: data

                }).then(function (result) {
                    if (result.status) {
                        if (result.url) {
                            location.replace(result.url)
                        }
                        else {
                            location.replace("/my/website/company")
                        }
                    }

                });
            }
            // if (tax_value == 'tax_exempt') {
            //     var file = $('input[name="exempt_certificate"]').prop('files')[0];
            //     if (!file) {
            //         $('.error_div').removeClass('d-none')
            //         $('.error_div').find('.error_mg').text('Kindly Tax Exempt Certificate.')
            //     }
            //     else {
            //         var msg = ("We are processing your request, please wait ...");
            //         $.blockUI({
            //             'message': '<h2 class="text-white"><img src="/web/static/img/spin.png" class="fa-pulse"/>' +
            //                 '    <br />' + msg +
            //                 '</h2>'
            //         });

            //         // var result = ev.target.result
            //         // var file_name = file.name
            //         // create_data['file_name'] = file_name
            //         // var valid_ext = ['xls', 'xlsx', 'csv']

            //         // var reader = new FileReader();
            //         reader.onload = function (ev) {
            //             var result = ev.target.result
            //             var file_name = file.name
            //             var create_data = {
            //                 file_name: file_name,
            //                 attachment_id: result.split(',')[1].trim()
            //             }
            //             data['document_data'] = create_data
            //             data['tax_exempt'] = tax_value
            //             $self._rpc({
            //                 route: "/update/business/tax",
            //                 params: data

            //             }).then(function (data) {

            //                 // $.unblockUI()
            //                 window.location.href = '/my/website/company'

            //             });
            //         }
            //         reader.readAsDataURL(file)



            //     }


            // }
        },
        _CloseModel: function (ev) {
            $('.sale_prompt').modal('hide')
        }

    });


    publicWidget.registry.SalePromot = publicWidget.Widget.extend({
        selector: '.sale_prompt',
        events: {
            'click .close': '_CloseModel',
            'change input[name="flexRadioDefault"]': '_taxSelection',
            'click .save_changes': '_saveChanges'
        },
        _saveChanges: function (ev) {
            var tax_value = $('input[name="flexRadioDefault"]:checked').val()
            var data = {}
            var reader = new FileReader();
            var $self = this
            if (!tax_value) {
                $('.error_div').removeClass('d-none')
                $('.error_div').find('.error_mg').text('Kindly Select the tax option.')
            }
            if (tax_value == 'tax_exempt') {
                var file = $('input[name="exempt_certificate"]').prop('files')[0];
                if (!file) {
                    $('.error_div').removeClass('d-none')
                    $('.error_div').find('.error_mg').text('Kindly Tax Exempt Certificate.')
                }
                else {
                    var msg = ("We are processing your request, please wait ...");
                    $.blockUI({
                        'message': '<h2 class="text-white"><img src="/web/static/img/spin.png" class="fa-pulse"/>' +
                            '    <br />' + msg +
                            '</h2>'
                    });

                    // var result = ev.target.result
                    // var file_name = file.name
                    // create_data['file_name'] = file_name
                    // var valid_ext = ['xls', 'xlsx', 'csv']

                    // var reader = new FileReader();
                    reader.onload = function (ev) {
                        var result = ev.target.result
                        var file_name = file.name
                        var create_data = {
                            file_name: file_name,
                            attachment_id: result.split(',')[1].trim()
                        }
                        data['document_data'] = create_data
                        data['tax_exempt'] = tax_value
                        $self._rpc({
                            route: "/update/business/tax",
                            params: data

                        }).then(function (data) {

                            // $.unblockUI()
                            window.location.href = '/my/website/company'

                        });
                    }
                    reader.readAsDataURL(file)



                }


            }
            else {
                var data = {
                    'create_data': false,
                    'tax_exempt': tax_value
                }
                $self._rpc({
                    route: "/update/business/tax",
                    params: data

                }).then(function (result) {
                    if (result.status) {
                        if (result.url) {
                            location.replace(result.url)
                        }
                        else {
                            location.replace("/my/website/company")
                        }
                    }

                });
            }
        },
        _taxSelection: function (ev) {

            var tax_value = $('input[name="flexRadioDefault"]:checked').val()
            if (tax_value == 'tax_exempt') {

                $('.exempt_file').removeClass('d-none')
            }
            else {
                $('.exempt_file').addClass('d-none')
            }
        },
        _CloseModel: function (ev) {
            $('.sale_prompt').modal('hide')
        }
    })





})

