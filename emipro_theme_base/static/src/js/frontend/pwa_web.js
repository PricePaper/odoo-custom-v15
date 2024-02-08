odoo.define('emipro_theme_base.pwa_web', function (require) {
"use strict";
    
    var html = document.documentElement;
    var utils = require('web.utils');
    var website_id = html.getAttribute('data-website-id') | 0;
    // Detects if device is on iOS
    const isIos = () => {
      const userAgent = window.navigator.userAgent.toLowerCase();
      return /iphone|ipad|ipod/.test( userAgent );
    }
    // Detects if device is in standalone mode
    const isInStandaloneMode = () => ('standalone' in window.navigator) && (window.navigator.standalone);

    // Checks if should display install popup notification:

    if (isIos() && !isInStandaloneMode()) {
        var iosPrompt = $(".ios-prompt");
        var ios_pwa = utils.get_cookie('ios_pwa');
        var pwa_cache_name = utils.get_cookie('pwa_cache_name');
        var is_pwa_enable = $('.is_pwa').val();
        if(!ios_pwa && is_pwa_enable) {
            iosPrompt.show();
            $(iosPrompt).click(function() {
                iosPrompt.remove();
                // Create a cookie to hide message in ios
                utils.set_cookie('ios_pwa', '1', 365*60*60*24);
            });
        }
        if(pwa_cache_name) {
            utils.set_cookie('ios_pwa', '1', 365*60*60*24);
        }
    }
    if ('serviceWorker' in navigator) {
        if(!navigator.onLine){
            var dv_offline = $('.ept_is_offline');
            if(dv_offline){
                dv_offline.show();
            }
        }
        navigator.serviceWorker.register('/service_worker').then(() => console.info('service worker registered'))
        .catch(error => {
          console.log('ServiceWorker registration failed: ', error)
        });
    }
});

