odoo.define('portal_enhancements.common', function (require) {
    'use strict';
    var core = require('web.core');

    var _t = core._t;
    var NameAndSignature = require('web.name_and_signature').NameAndSignature;

    const publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    $.blockUI.defaults.css.border = '0';
    $.blockUI.defaults.css["background-color"] = '';
    $.blockUI.defaults.overlayCSS["opacity"] = '0.9';

    function validateEmail($email) {
        var emailReg = /^([\w-\.]+@([\w-]+\.)+[\w-]{2,4})?$/;
        return emailReg.test($email);
    }


    var SignatureForm = publicWidget.Widget.extend({
        template: 'portal.portal_signature',
        xmlDependencies: ['/portal/static/src/xml/portal_signature.xml'],
        events: {
            'click .o_portal_sign_submit': 'async _onClickSignSubmit',
        },
        custom_events: {
            'signature_changed': '_onChangeSignature',
        },

        /**
         * Overridden to allow options.
         *
         * @constructor
         * @param {Widget} parent
         * @param {Object} options
         * @param {string} options.callUrl - make RPC to this url
         * @param {string} [options.sendLabel='Accept & Sign'] - label of the
         *  send button
         * @param {Object} [options.rpcParams={}] - params for the RPC
         * @param {Object} [options.nameAndSignatureOptions={}] - options for
         *  @see NameAndSignature.init()
         */
        init: function (parent, options) {
            this._super.apply(this, arguments);

            this.csrf_token = odoo.csrf_token;

            this.callUrl = options.callUrl || '';
            this.rpcParams = options.rpcParams || {};
            this.sendLabel = options.sendLabel || _t("Accept & Sign");

            this.nameAndSignature = new NameAndSignature(this,
                options.nameAndSignatureOptions || {});
        },
        /**
         * Overridden to get the DOM elements
         * and to insert the name and signature.
         *
         * @override
         */
        start: function () {
            var self = this;
            this.$confirm_btn = this.$('.o_portal_sign_submit');
            this.$controls = this.$('.o_portal_sign_controls');
            var subWidgetStart = this.nameAndSignature.replace(this.$('.o_web_sign_name_and_signature'));
            return Promise.all([subWidgetStart, this._super.apply(this, arguments)]).then(function () {
                self.nameAndSignature.resetSignature();
            });
        },

        //----------------------------------------------------------------------
        // Public
        //----------------------------------------------------------------------

        /**
         * Focuses the name.
         *
         * @see NameAndSignature.focusName();
         */
        focusName: function () {
            this.nameAndSignature.focusName();
        },
        /**
         * Resets the signature.
         *
         * @see NameAndSignature.resetSignature();
         */
        resetSignature: function () {
            return this.nameAndSignature.resetSignature();
        },

        //----------------------------------------------------------------------
        // Handlers
        //----------------------------------------------------------------------

        /**
         * Handles click on the submit button.
         *
         * This will get the current name and signature and validate them.
         * If they are valid, they are sent to the server, and the reponse is
         * handled. If they are invalid, it will display the errors to the user.
         *
         * @private
         * @param {Event} ev
         * @returns {Deferred}
         */
        _onClickSignSubmit: function (ev) {

            console.log('helllooooo')
            var self = this;
            ev.preventDefault();

            if (!this.nameAndSignature.validateSignature()) {
                return;
            }

            var name = this.nameAndSignature.getName();
            var signature = this.nameAndSignature.getSignatureImage()[1];

            var msg = ("We are processing your request, please wait ...");
            $.blockUI({
                'message': '<h2 class="text-white"><img src="/web/static/img/spin.png" class="fa-pulse"/>' +
                    '    <br />' + msg +
                    '</h2>'
            });

            var credit_application = $('.credit_application').length
            var ach_debit_form = $('.ach_debit_application').length
            if (credit_application) {

                var data = {}
                var flag = false
                var bank_data = []
                var bank_flag = flag
                var trade_data = []
                var trade_flag = false
                var officer_data = []
                var officer_flag = false

                $('.main_info_data').each(function () {
                    $(this).find('input').each(function () {
                        if (!$(this).val()) {
                            $(this).addClass('is-invalid')
                            $(this).focus()
                            flag = true
                        }
                        else {

                            $(this).removeClass('is-invalid')
                            data[$(this).attr('name')] = $(this).val()
                        }
                    })
                }).promise().done(function () {
                    console.log(data)
                    if (flag) {
                        $.unblockUI();
                    }
                    else {
                        console.log('hello12')
                        $('.bank_list .bank_row').each(function () {
                            var bank_data_dict = {}
                            $(this).find('input').each(function () {
                                if (!$(this).val()) {
                                    $(this).addClass('is-invalid')
                                    $(this).focus()
                                    bank_flag = true
                                }
                                bank_data_dict[$(this).attr('name')] = $(this).val()
                            }).promise().done(function () {
                                bank_data.push(bank_data_dict)
                            })

                        }).promise().done(function () {
                            console.log(bank_data)
                            if (bank_flag) {
                                $.unblockUI();
                            }
                            else {
                                $('.trade_list .trade_row').each(function () {
                                    var trade_data_dict = {}
                                    $(this).find('input').each(function () {
                                        if (!$(this).val()) {
                                            $(this).addClass('is-invalid')
                                            $(this).focus()
                                            trade_flag = true
                                        }
                                        trade_data_dict[$(this).attr('name')] = $(this).val()
                                    }).promise().done(function () {
                                        trade_data.push(trade_data_dict)
                                    })

                                }).promise().done(function () {
                                    if (trade_flag) {
                                        $.unblockUI();
                                    }
                                    else {

                                        $('.officers_list .officer_row').each(function () {
                                            var off_data_dict = {}
                                            $(this).find('input').each(function () {
                                                if (!$(this).val()) {
                                                    $(this).addClass('is-invalid')
                                                    $(this).focus()
                                                    officer_flag = true
                                                }
                                                off_data_dict[$(this).attr('name')] = $(this).val()
                                            }).promise().done(function () {
                                                officer_data.push(off_data_dict)
                                            })

                                        }).promise().done(function () {
                                            if (officer_flag) {
                                                $.unblockUI();
                                            }
                                            else {
                                                console.log('main_complete')
                                                data['bank_data'] = bank_data
                                                data['trade_data'] = trade_data
                                                data['officer_data'] = officer_data
                                                console.log(data)
                                                data['signature'] = signature
                                                data['print_name'] = name
                                                ajax.jsonRpc('/my/credit/submit', 'call', {
                                                    data: data,


                                                }).then(function (data) {

                                                    window.location = '/my/website/company'
                                                })


                                            }
                                        })
                                    }
                                })
                            }
                        })
                    }
                })



            }
            if (ach_debit_form) {
                var data = {}
                var flag = false
                $('.main_info_data input').each(function () {




                    if (!$(this).val()) {
                        $(this).addClass('is-invalid')
                        $(this).focus()
                        flag = true
                    }
                    else {

                        $(this).removeClass('is-invalid')
                        data[$(this).attr('name')] = $(this).val()
                    }

                }).promise().done(function () {
                    if (flag) {
                        $.unblockUI();
                    }
                    else {
                        data['signature'] = signature
                        data['print_name'] = name
                        ajax.jsonRpc('/my/ach/submit', 'call', {
                            data: data,


                        }).then(function (data) {

                            window.location = '/my/website/company'
                        })
                    }

                })
            }

        },
        /**
         * Toggles the submit button depending on the signature state.
         *
         * @private
         */
        _onChangeSignature: function () {
            var isEmpty = this.nameAndSignature.isSignatureEmpty();
            this.$confirm_btn.prop('disabled', isEmpty);
        },
    });

    publicWidget.registry.SignatureForm = publicWidget.Widget.extend({
        selector: '.o_portal_signature_form_new',

        /**
         * @private
         */
        start: function () {
            var hasBeenReset = false;

            var callUrl = this.$el.data('call-url');
            var nameAndSignatureOptions = {
                defaultName: this.$el.data('default-name'),
                mode: this.$el.data('mode'),
                displaySignatureRatio: this.$el.data('signature-ratio'),
                signatureType: this.$el.data('signature-type'),
                fontColor: this.$el.data('font-color') || 'black',
            };
            var sendLabel = this.$el.data('send-label');

            var form = new SignatureForm(this, {
                callUrl: callUrl,
                nameAndSignatureOptions: nameAndSignatureOptions,
                sendLabel: sendLabel,
            });

            // Correctly set up the signature area if it is inside a modal
            this.$el.closest('.modal').on('shown.bs.modal', function (ev) {
                if (!hasBeenReset) {
                    // Reset it only the first time it is open to get correct
                    // size. After we want to keep its content on reopen.
                    hasBeenReset = true;
                    form.resetSignature();
                } else {
                    form.focusName();
                }
            });

            return Promise.all([
                this._super.apply(this, arguments),
                form.appendTo(this.$el)
            ]);
        },
    });



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
            else {
                data = {
                    'payment_value': payment_value
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
            $('.payment_prompt').modal('hide')
        }

    });

    publicWidget.registry.CreditApplication = publicWidget.Widget.extend({
        selector: '.credit_application',
        events: {
            'click .add_officers': '_addofficer',
            'click .delete_officer': '_deleteOfficer',
            'click .add_Bank': '_addBank',
            'click .add_trade': '_addtrade',

        },
        _deleteOfficer: function (ev) {
            $(ev.currentTarget).parent('.deleteable').siblings('.deleteable_hr').remove()
            $(ev.currentTarget).parent('.deleteable').remove()
        },
        _addtrade: function (ev) {
            $(ev.currentTarget).parents('.trade_list').find('.trade_row').append(`
                <hr class='deleteable_hr'/>
                 <div class='main_row deleteable row position-relative'>
                <a class='delete_officer text-danger position-absolute' style='right:0;z-index:99'>
                        <i class='fa fa-trash'/>
                    </a>
                    <div class="form-group col-xl-4">
                                <label for="name">Name:</label>

                                <input type="text" class="form-control" name="name" required="True"/>
                            </div>
                            <div class="form-group col-xl-4">
                                <label for="phone">Phone:</label>

                                <input type="text" class="form-control" name="phone"/>
                            </div>

                             <div class="form-group col-xl-4">
                                <label for="fax">fax:</label>

                                <input type="text" class="form-control" name="fax"/>
                            </div>



                            <div class='form-group col-xl-3'>
                                <label for='address'>Address:</label>
                                <input type='text' t-att-value='partner.street' class='form-control' name='address'/>
                            </div>

                            <div class='form-group col-xl-3'>
                                <label for='city'>city:</label>
                                <input type="city" t-att-value='partner.city' class="form-control" name="city"/>
                            </div>

                            <div class='form-group col-xl-3'>
                                <label for='state'>State:</label>
                                <input type="state" t-att-value='partner.state_id' class="form-control" name="state"/>
                            </div>

                            <div class='form-group col-xl-3'>
                                <label for='zip'>Zip:</label>
                                <input type="zip" t-att-value='partner.zip' class="form-control" name="zip"/>
                            </div>



                        </div><hr class='deleteable_hr'/>
                `)
        },
        _addBank: function (ev) {
            $(ev.currentTarget).parents('.bank_list').find('.bank_row').append(`
                <hr class='deleteable_hr'/>
                <div class='main_row deleteable row position-relative'>
                <a class='delete_officer text-danger position-absolute' style='right:0;z-index:99'>
                        <i class='fa fa-trash'/>
                    </a>
                            <div class="form-group col-xl-6">
                                <label for="name">Bank:</label>

                                <input type="text" class="form-control" name="name" required="True"/>
                            </div>
                            <div class="form-group col-xl-6">
                                <label for="Acc.#">Acc.#:</label>

                                <input type="text" class="form-control" name="acc"/>
                            </div>

                            <div class='form-group col-xl-3'>
                                <label for='address'>Address:</label>
                                <input type='text' t-att-value='partner.street' class='form-control' name='address'/>
                            </div>

                            <div class='form-group col-xl-3'>
                                <label for='city'>city:</label>
                                <input type="city" t-att-value='partner.city' class="form-control" name="city"/>
                            </div>

                            <div class='form-group col-xl-3'>
                                <label for='state'>State:</label>
                                <input type="state" t-att-value='partner.state_id' class="form-control" name="state"/>
                            </div>

                            <div class='form-group col-xl-3'>
                                <label for='zip'>Zip:</label>
                                <input type="zip" t-att-value='partner.zip' class="form-control" name="zip"/>
                            </div>
                            <div class='form-group col-xl-4'>
                                <label for='officer_name'>Officer Familiar with A/c </label>
                                <input type="officer_name"  class="form-control" name="officer_name"/>
                            </div>
                            <div class='form-group col-xl-4'>
                                <label for='office_phone'>Phone:</label>
                                <input type="office_phone"  class="form-control" name="office_phone"/>
                            </div>
                            <div class='form-group col-xl-4'>
                                <label for='offier_fax'>Fax:</label>
                                <input type="offier_fax"  class="form-control" name="offier_fax"/>
                            </div>


                        </div><hr class='deleteable_hr'/>
    `)
        },
        _addofficer: function (ev) {
            $(ev.currentTarget).parents('.officers_list').find('.officer_row').append(`
                <hr class='deleteable_hr'/>
                <div class='main_row deleteable row position-relative'>
                    <a class='delete_officer text-danger position-absolute' style='right:0;z-index:99'>
                        <i class='fa fa-trash'/>
                    </a>
                    <div class="form-group col-xl-6">
                        
                        <label for="name">Name:</label>

                        <input type="text" class="form-control"  name="name" required="True"/>
                    </div>
                    <div class="form-group col-xl-6">
                        <label for="title">Title:</label>

                        <input type="text" class="form-control" name="title"/>
                    </div></div><hr class='deleteable_hr'/>`)
        }
    })

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

