odoo.define('theme_clarico_vega.drift_zoom', function (require) {
    "use strict";
    require('website_sale.website_sale');
    var publicWidget = require('web.public.widget');
    const {_t} = require('web.core');

    publicWidget.registry.WebsiteSale.include({
        /* Prevent Default zoom */
        _startZoom: function() {
            var self = this;
            var zoom_enable = $('.drift_zoom').val();
            if (zoom_enable) {
                var DriftZoom = new publicWidget.registry.driftZoom();
                const className = _t.database.parameters.direction === 'rtl' ? 'te-rtl' : 'te';
                this.images = _.each($('.product_detail_img'), function (el) {
                    var delay = 0;
                    if($( window ).width() > 991) {
                        delay = 400;
                    }
                    var imageVals = {
                        namespace: className,
                        sourceAttribute: 'src',
                        paneContainer: document.getElementById("mainSlider"),
                        inlinePane: 992,
                        inlineOffsetY: -50,
                        touchDelay: delay,
                    };
                    const drift = new Drift(el, imageVals);
                    DriftZoom.destroySwipe();
                    return drift;
                });
            }
        },
    });
    
    publicWidget.registry.driftZoom = publicWidget.Widget.extend({
        selector: '#mainSlider',
        disabledInEditableMode: true,
        events: {
            'touchstart': 'destroySwipe',
        },
        destroySwipe: function(ev) {
            if($('.drift-zoom-pane').length) {
                // Prevent carousel swipe
                ev.stopPropagation();
                ev.preventDefault();
            }

        },
    });
    
});
