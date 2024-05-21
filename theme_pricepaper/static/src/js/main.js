odoo.define('theme_pricepaper.common', function (require) {
    'use strict';
    var core = require('web.core');
    const publicWidget = require('web.public.widget');
    const config = require('web.config');
    const dynamic_snippt = require('website.s_dynamic_snippet')
    var ajax = require('web.ajax');
    function validateEmail($email) {
        var emailReg = /^([\w-\.]+@([\w-]+\.)+[\w-]{2,4})?$/;
        return emailReg.test($email);
    }
    dynamic_snippt.include({
        _getQWebRenderOptions: function () {
            var numberOfElements = 5
            if (config.device.isMobile) {
                numberOfElements = this.$target[0].dataset.numberOfElementsSmallDevices
            } else {
                if (window.innerWidth <= 1024 && window.innerWidth > 950) {
                    numberOfElements = 3
                }
                else if (window.innerWidth <= 950 && window.innerWidth > 760) {
                    numberOfElements = 2
                }
                else {

                    numberOfElements = this.$target[0].dataset.numberOfElements
                }
            }
            return {
                chunkSize: parseInt(
                    16
                ),
                data: this.data,
                uniqueId: this.uniqueId
            };
        },
        _render: function () {
            this._super.apply(this, arguments);
            $('.paper_container').find('.carousel-item .row').addClass('owl-carousel')
            $('.paper_container').find('.carousel-item .row').find('.col-0').addClass('item')
            $('.paper_container .carousel-item .row').owlCarousel({
                loop: true,
                margin: 20,
                nav: false,
                dots: false,
                autoplay: true,
    
                responsive: {
                    0: {
                        items: 1
                    },
                    450: {
                        items: 1
                    },
                    600: {
                        items: 2
                    },
                    1000: {
                        items: 3
                    },
                    1200: {
                        items: 4
                    },
                    1700: {
                        items: 5
                    }
    
                }
            })
    
        }

    })
    publicWidget.registry.Crmform = publicWidget.Widget.extend({
        selector: '.home-contact-form',
        events: {
            'click button[type=submit]': '_onFormSubmit',

        },
        start: function () {
            // var self = this
            ajax.jsonRpc('/gen/captcha', 'call', {}).then(function (result) {
                if (result.status) {
                    console.log(result)
                    $('.home-contact-form').find('button[type=submit]').parent().before(result.template)
                    grecaptcha.ready(function () {
                        grecaptcha.render("place_captcha", {
                            sitekey: $('#place_captcha').attr('data-sitekey')
                        });
                    });

                }
            })
            return this._super(...arguments);

        },
        _onFormSubmit: function (ev) {
            var curr = $(ev.currentTarget)
            curr.prop('disabled', true)
            ev.preventDefault()
            ev.stopPropagation();
            if (!$("#g-recaptcha-response").val()) {
                $('.captcha_warning').remove()
                $(ev.currentTarget).parent().before(`<div class='col-12 captcha_warning'><p style="font-size:13px" class='text-danger'>Please Enter Captcha</p></div>`);
                curr.prop('disabled', false)
                return
            }
            $('.captcha_warning').remove()
            var $form = $(this.$target).find('form')
            var data = {}
            var flag = false
            var validRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;
            $form.find('input:not(.d-none),textarea:not(#g-recaptcha-response)').each(function () {

                if (!$(this).val()) {

                    $(this).get(0).setCustomValidity('Please Enter Correct Information');
                    $(this).get(0).reportValidity()
                    flag = true
                    curr.prop('disabled', false)
                    return
                }
                else {

                    if ($(this).attr('name') == 'email' && !(validateEmail($(this).val()))) {
                        $(this).get(0).setCustomValidity('Please Enter Correct Email');
                        $(this).get(0).reportValidity()
                        flag = true

                        curr.prop('disabled', false)
                        return

                    }

                    data[$(this).attr('name')] = $(this).val()
                }

            }).promise().done(function () {
                if (!flag) {

                    ajax.jsonRpc('/contact/crm/lead', 'call', data).then(function (result) {
                        if (result.status) {
                            $form.replaceWith("<strong> Thanks for contacting us , Our team will get back to you shortly</strong>")
                        }
                    })
                }
            })
        }
    })
    $(document).ready(function () {




        $(document).on('click', '.scroll_div .left_scrol', function (ev) {



            var main_row = $(ev.currentTarget).parents('.paper_container').find('.carousel-item .row')
            main_row.find('.owl-next').click()
           
        })

        if ($('#wrapwrap').hasClass('odoo-editor-editable')) {
            $('.we-serve').addClass('d-flex')
        }
        else {

            $('.we-serve').owlCarousel({
                loop: true,
                margin: 10,
                nav: true,
                dots: false,
                autoplay: true,

                responsive: {
                    0: {
                        items: 2
                    },
                    600: {
                        items: 3
                    },
                    1100: {
                        items: 4
                    },

                }
            })
        }
    })
});
