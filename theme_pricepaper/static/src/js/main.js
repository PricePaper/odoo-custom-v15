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
            $form.find('input,textarea').each(function () {
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
        setInterval(function(){
            $('.scroll_div .left_scrol').click()
        },3000)
        $(document).on('click', '.scroll_div .left_scrol', function (ev) {
            var main_row = $(ev.currentTarget).parents('.paper_container').find('.carousel-item .row')
            var newScrollLeft = main_row.scrollLeft();
            // var divWidth = main_row.outerWidth();
            // var $width = main_row.outerWidth()
            // var $scrollWidth = main_row[0].scrollWidth;
            // var $scrollLeft = main_row.scrollLeft();

            var newScrollLeft = main_row.scrollLeft(),
                width = main_row.width(),
                scrollWidth = main_row.get(0).scrollWidth;
            var offset = 8;
                
            if (scrollWidth - newScrollLeft - width <= offset) {
                var left = 0
            }







            else {


                var left = main_row.scrollLeft() + main_row.find('.col-0').first().width() + parseInt(main_row.find('.col-0').first().css('padding-right').replace('px',''))
            }
            var $self = $(ev.currentTarget)
            $self.prop('disabled',true)
            main_row.animate({
                scrollLeft: left
            }, {
                duration:400,
                complete:function(){
                    $self.prop('disabled',false)
                }
            });




            // main_row.scrollLeft(main_row.scrollLeft()+460)
        })
        // let items = document.querySelectorAll('.carousel .carousel-item')

        // items.forEach((el) => {
        //     const minPerSlide = 4
        //     let next = el.nextElementSibling
        //     for (var i = 1; i < minPerSlide; i++) {
        //         if (!next) {
        //             // wrap carousel by using first child
        //             next = items[0]
        //         }
        //         let cloneChild = next.cloneNode(true)
        //         el.appendChild(cloneChild.children[0])
        //         next = next.nextElementSibling
        //     }
        // })
        if ($('#wrapwrap').hasClass('odoo-editor-editable')) {
            $('.owl-carousel').addClass('d-flex')
        }
        else {

            $('.owl-carousel').owlCarousel({
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
