odoo.define('theme_clarico_vega.mixins', function (require) {
'use strict';

    var OwlMixin = {
        initOwlCarousel: function (cls, margin, responsive, loop, items, dots, nav, mouseDrag, touchDrag, pullDrag, center, autoplay, rewind) {
            var owl_rtl = false;
            if ($('#wrapwrap').hasClass('o_rtl')) {
                owl_rtl = true;
            }
            var margin = margin ? margin : 10;
            var owlCarousel = cls ? $(cls) : $(".owl-carousel");
            owlCarousel.owlCarousel({
                loop: loop,
                margin: margin,
                lazyLoad: true,
                nav: nav,
                autoplay: autoplay,
                center: center,
                dots: dots,
                rtl: owl_rtl,
                items: items,
                rewind: rewind,
                autoplayHoverPause: true,
                autoplayTimeout: 4000,
                mouseDrag: mouseDrag,
                touchDrag: touchDrag,
                pullDrag: pullDrag,
                navText: ['<i class="fa fa-angle-left"></i>', '<i class="fa fa-angle-right"></i>'],
                responsive: responsive
            });
        },
    };
    return OwlMixin;
});