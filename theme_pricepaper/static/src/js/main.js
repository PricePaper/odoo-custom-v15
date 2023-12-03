odoo.define('theme_pricepaper.common', function (require) {
    'use strict';
    $(document).ready(function () {
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
