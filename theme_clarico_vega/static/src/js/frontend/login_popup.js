odoo.define('theme_clarico_vega.login_popup', function(require) {
    "use strict";

    var sAnimations = require('website.content.snippets.animation');
    var ajax = require('web.ajax');

    sAnimations.registry.login_popup = sAnimations.Class.extend({
        selector: "#wrapwrap",
        events: {
            'click .o_action': '_onClickAction',
            'submit #loginRegisterPopup .oe_login_form': '_customerLogin', // on submit of login form from popup
            'submit #loginRegisterPopup .oe_signup_form': '_customerRegistration', // on submit of signup form from popup
            'submit #loginRegisterPopup .oe_reset_password_form': '_resetPassword' // on submit of reset password form from popup
        },
        start: function() {
            var self = this;
        },

        _customerLogin: function(e) {
            e.preventDefault()
            var $form = $(e.currentTarget)
            $.ajax({
                url: '/web/login',
                type: 'POST',
                data: $($form).serialize(),
                async: false,
                success: function(data) {
                    var data_main = JSON.parse(data)
                    if (data_main.login_success && data_main.redirect) {
                        if (data_main.redirect != '1') {
                            $("#loginRegisterPopup .oe_login_form .alert-success-error .alert-danger").removeClass('d-none').addClass('d-none');
                            if (typeof data_main.hide_msg != 'undefined' && !data_main.hide_msg) {
                                $("#loginRegisterPopup .oe_login_form .alert-success-error .alert-success").removeClass('d-none');
                            }
                            window.location.replace(data_main.redirect)
                        } else {
                            $("#loginRegisterPopup .oe_login_form .alert-success-error .alert-danger").removeClass('d-none').addClass('d-none');
                            $("#loginRegisterPopup .oe_login_form .alert-success-error .alert-success").removeClass('d-none');
                            window.location.reload()
                        }
                    } else if (!data_main.login_success && data_main.error) {
                        $("#loginRegisterPopup .oe_login_form .alert-success-error .alert-success").removeClass('d-none').addClass('d-none');
                        $("#loginRegisterPopup .oe_login_form .alert-success-error .alert-danger").html(data_main.error).removeClass('d-none');
                    }
                },
                error: function(data) {
                    console.log('An error occurred.')
                },
            });
        },

        _customerRegistration: function(e) {
            e.preventDefault()
            var $form = $(e.currentTarget)
            $.ajax({
                url: '/web/signup',
                type: 'POST',
                data: $($form).serialize(),
                async: false,
                success: function(data) {
                    var data_main = JSON.parse(data)
                    if (data_main.login_success && data_main.redirect) {
                        $("#loginRegisterPopup .oe_signup_form .alert-success-error .alert-danger").removeClass('d-none').addClass('d-none');
                        $("#loginRegisterPopup .oe_signup_form .alert-success-error .alert-success").removeClass('d-none');
                        window.location.reload()
                    } else if (!data_main.login_success && data_main.error) {
                        $("#loginRegisterPopup .oe_signup_form .alert-success-error .alert-success").removeClass('d-none').addClass('d-none');
                        $("#loginRegisterPopup .oe_signup_form .alert-success-error .alert-danger").html(data_main.error).removeClass('d-none');
                    }
                },
                error: function(data) {
                    console.log('An error occurred.')
                },
            });
        },

        _resetPassword: function(e) {
            e.preventDefault()
            var $form = $(e.currentTarget)
            $.ajax({
                url: '/web/reset_password',
                type: 'POST',
                data: $($form).serialize(),
                async: false,
                success: function(data) {
                    var data_main = JSON.parse(data)
                    if (data_main.error) {
                        $("#loginRegisterPopup .oe_reset_password_form .alert-success-error").html('<p class="alert alert-danger">' + data_main.error + '</p>')
                    } else if (data_main.message) {
                        $("#loginRegisterPopup .oe_reset_password_form .alert-success-error").html('<p class="alert alert-success">' + data_main.message + '</p>')
                    }
                },
                error: function(data) {
                    console.log('An error occurred.')
                },
            });
        },
    });
    $(document).ready(function() {
        /** Login / Signup Popup **/
        $(document).on('click', '.te_signin', function() {
            $("#loginRegisterPopup").modal();
            $('body').find('.modal-backdrop').css('position', 'relative');
        });

        $("#loginRegisterPopup .oe_reset_password_form").hide();
        $("#loginRegisterPopup .open_reset_password").click(function() {
            $("#loginRegisterPopup .oe_login_form").hide();
            $("#loginRegisterPopup .oe_reset_password_form").show();
        });
        $("#loginRegisterPopup .back_login").click(function() {
            $("#loginRegisterPopup .oe_reset_password_form").hide();
            $("#loginRegisterPopup .oe_login_form").show();
        });
    });
});
