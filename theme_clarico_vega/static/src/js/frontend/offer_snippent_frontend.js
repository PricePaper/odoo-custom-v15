//---------------------------------------------------------
// Countdown For offer timer snippet
//---------------------------------------------------------
odoo.define('theme_clarico_vega.front_js', function(require) {
    'use strict';
    var sAnimation = require('website.content.snippets.animation');
    var ajax = require("web.ajax");

    sAnimation.registry.js_timer = sAnimation.Class.extend({
        selector: ".js_timer",
        start: function() {
            this.redrow();
        },
        stop: function() {
            this.clean();
        },
        redrow: function(debug) {
            this.clean(debug);
            this.build(debug);
        },
        clean: function(debug) {
            this.$target.empty();
        },
        build: function(debug) {
            var self = this;
            var date = self.$target.data("date");

            if (date != "nan") {
                var countDownDate = new Date(date).getTime();
                var x = setInterval(function() {

                    // Get todays date and time
                    var now = new Date().getTime();

                    // Find the distance between now an the count down date
                    var distance = countDownDate - now; // Time calculations for days, hours, minutes and seconds

                    if (distance > 0) {
                        var days = Math.floor(distance / (1000 * 60 * 60 * 24));
                        var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                        var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                        var seconds = Math.floor((distance % (1000 * 60)) / 1000);

                        if ((seconds + '').length == 1) {
                            seconds = "0" + seconds;
                        }
                        if ((days + '').length == 1) {
                            days = "0" + days;
                        }
                        if ((hours + '').length == 1) {
                            hours = "0" + hours;
                        }
                        if ((minutes + '').length == 1) {
                            minutes = "0" + minutes;
                        }
                    }
                    // If the count down is over, write some text
                    if (distance <= 0) {
                        clearInterval(x);
                        seconds = "00";
                        days = "00";
                        minutes = "00";
                        hours = "00";
                        $('.js_timer_div').empty();
                    }
                    if (self.$target.find(".snippet_right_timer_div")) {
                        self.$target.find(".snippet_right_timer_div").remove()
                        var append_data = "<div class='snippet_right_timer_div text-left mt16 date_time'><span class='col-lg-3 col-md-2 col-sm-2 col-3 text-center d-inline-block p-0'><div class='rounded_digit py-3'><span id='days' class='d-block  te_days_hr_min_sec_digit  o_default_snippet_text'>" + days + "</span><span id='d_lbl' class='d-block'>Days</span></div></span><span class='col-lg-3 col-md-2 col-sm-2 col-3 text-center d-inline-block p-0'><div class='rounded_digit py-3'><span id='hours' class='d-block  te_days_hr_min_sec_digit o_default_snippet_text'>" + hours + "</span><span id='h_lbl' class='d-block'>Hrs</span></div></span><span class='col-lg-3 col-md-2 col-sm-2 col-3 text-center d-inline-block p-0'><div class='rounded_digit py-3'><span id='minutes' class='d-block te_days_hr_min_sec_digit  o_default_snippet_text'>" + minutes + "</span><span id='m_lbl' class=' d-block'>Mins</span></div></span><span class='col-lg-3 col-md-2 col-sm-2 col-3 text-center d-inline-block p-0'><div class='rounded_digit py-3'><span id='seconds' class='d-block te_days_hr_min_sec_digit o_default_snippet_text'>" + seconds + "</span><span id='s_lbl' class='d-block'>Secs</span></div></span></div>";
                        self.$target.find(".snippet_right_timer_div").css("display", "block")
                        self.$target.append(append_data)
                    }
                }, 1000);
            }
        }
    });
});
