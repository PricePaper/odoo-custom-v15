/**************************************************
        01. Multi Item Carousel
**************************************************/

//------------------------------------------
// 01. Multi Item Carousel
//------------------------------------------

odoo.define('theme_clarico_vega.multi_item_carousel', function(require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    publicWidget.registry.multi_carousel = publicWidget.Widget.extend({
        selector: "#wrapwrap",
        start: function() {
            this.multi_carousel();
        },
        multi_carousel: function() {
            $('#carousel_recently_view .carousel-inner').find("div[data-active=True]").remove();
            $(".carousel").swipe({
                swipe: function(event, direction, distance, duration, fingerCount, fingerData) {
                    if (direction == 'left') $(this).carousel('next');
                    if (direction == 'right') $(this).carousel('prev');
                },
                allowPageScroll:"vertical"
            });
            $('.common_carousel_emp_ept').carousel({
              interval: 1000
            });
            $('.common_carousel_emp_ept .carousel-item').each(function(){
                var next = $(this).next();
                if (!next.length) {
                    next = $(this).siblings(':first');
                }
                $(this).children().not(':first').remove();
                next.children(':first-child').clone().appendTo($(this));

                for (var i=0;i<4;i++) {
                    next=next.next();
                    if (!next.length) {
                        next = $(this).siblings(':first');
                    }
                    next.children(':first-child').clone().appendTo($(this));
                }
            });
        },
    });
});
