/*******************************************
INDEX: 01. Video Popup Activation
********************************************/
odoo.define('theme_clarico_vega.popup', function(require) {
    'use strict';
    require('web.dom_ready');

    var imagePopup = $('.popup-btn');
    var videoPopup = $('.video-popup');
    imagePopup.magnificPopup({
        type: 'image',
        gallery: {
            enabled: true
        }
    });
    videoPopup.magnificPopup({
        type: 'iframe',
        fixedContentPos: false,
        closeMarkup: '<button type="button" class="custom-close mfp-close"><i class="dl-icon-close mfp-close"></i></button type="button">'
    });
});
