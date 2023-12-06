odoo.define('emipro_theme_base.banner_video', function(require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    publicWidget.registry.js_banner_video = publicWidget.Widget.extend({
        selector: ".js_banner_video",
        start: function () {
            this.redrow();
        },
        stop: function () {
            this.clean();
        },
        redrow: function (debug) {
            this.clean(debug);
            this.build(debug);
        },
        clean: function (debug) {
            this.$target.empty();
        },
        build: function (debug) {
            var self = this;
            var is_ios = false
            if (navigator.userAgent.search("Safari") >= 0 && navigator.userAgent.search("Chrome") < 0) {
                 is_ios = true
            }
            ajax.jsonRpc('/get_banner_video_data', 'call', {'is_ios': is_ios}).then(function (data) {
                $(self.$target).html(data);
                var video = $("video");
                $.each(video, function(){
                   this.controls = false;
                });
            });
        }
    });
})
