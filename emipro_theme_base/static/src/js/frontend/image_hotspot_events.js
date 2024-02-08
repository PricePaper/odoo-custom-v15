odoo.define('emipro_theme_base.image_hotspot_events',function(require){
    'use strict';
    var ajax = require('web.ajax');
    var core = require('web.core');
    const session = require('web.session');
    var _t = core._t;
    var timeout;
    require('web.dom_ready');

    /*Hide Popover for website user(Unregistered) if hotspot is not assigned any product or URL*/
    if (session.is_website_user) {
        $('.hotspot_element').each(function(i,e) {
            if(!$(this).data('product_id') && !$(this).data('url')){
                $(this).remove()
            }
        });
    };

    $("body img").each( function() {
        var hotspot = $(this).parent().find('img~.hotspot_element:visible')
        if(hotspot.length) {
            bindEvents(hotspot);
        }
    });

    // Bind Events of Hotspot Elements
    function bindEvents(e) {
        $(e).each(function(i,e) {
            if($(e).data('url')) {
                $("#"+e.id).bind($(e).data('event'), function () {
                    if(!$('body').hasClass('editor_enable')) {
                        var a = document.createElement('a')
                        a.id = e.id
                        a.href = $(e).data('url')
                        a.target = "_blank"
                        a.click()
                    }
                })
            } else if($(e).data('product_id')) {
                $("#"+e.id).bind($(e).data('event'), function () {
                    if(!$('body').hasClass('editor_enable')) {
                        var a = document.createElement('a')
                        if($(e).data('action') == "display_product") {
                            a.id = e.id
                            a.classList.value = "quick-view-a"
                            a.setAttribute('data-id',$(e).data('product_id'))
                            $('div#wrapwrap').append(a)
                        } else if ($(e).data('action') == "add_to_cart") {
                            appendPopover(e)
                            hotspotPopover(e)
                            return
                        } else {
                            a.id = e.id
                            a.href = document.location.origin+'/shop/'+$(e).data('product_id')
                            a.target = "_blank"
                        }
                        a.click()
                    }
                })
            } else if($(e).data('action') == "add_to_cart" && !$(e).data('product_id')) {
                appendPopover(e)
                $("#"+e.id).bind($(e).data('event'), function () {
                    var a = document.createElement('a')
                    hotspotPopover(e)
                })
            }

        });
    };

    function appendPopover(e) {
        $(e).popover({
            trigger: 'manual',
            animation: false,
            html: true,
            sanitize: false,
            container: 'body',
            placement: 'bottom',
            template: '<div class="popover hotspot-popover" role="tooltip"><div class="arrow"></div><h3 class="popover-header"></h3><div class="popover-body"></div></div>'
        });
    };

    function hotspotPopover(e) {
        var self = this;
        clearTimeout(timeout);
        $('.hotspot_element').not(e).popover('hide');
        timeout = setTimeout(function () {
            if ($('.hotspot-popover:visible').length) {
                return;
            }
            ajax.jsonRpc('/get-pop-up-product-details', 'call',{
                'product': parseInt($(e).data("product_id")),
            }).then(function(data) {
                $(e).data("bs.popover").config.content = data;
                $(e).popover("show");
                if($(e).data('event') != 'click') {
                    $('.popover').on('mouseleave', function () {
                        $('.hotspot-popover').popover('hide');
                    });
                    $(e).on('mouseleave', function () {
                        setTimeout(function () {
                            if (!$(".popover:hover").length) {
                                $('.hotspot-popover').popover('hide');
                            }
                        }, 300);
                    });
                }
            });
        }, 100);
    }

    // Body click event to remove pop over from hotspot
    $("body").click(function(e) {
        $('.hotspot-popover').each(function () {
            // hide any open popovers when the anywhere else in the body is clicked
            if(!$(e.target).hasClass('popover-body') && !$(e.target).hasClass('hotspotImage') && !$(e.target).parents('.popover-body').length && !$('body').hasClass('editor_enable')) {
                $(this).popover('hide');
            }
        });
    });

    function hidePopover(ev) {
        ev.stopImmediatePropagation();
        $('.hotspot-popover').popover('hide');
    }
    window.addEventListener('scroll', _.debounce(hidePopover,400), true);

});
