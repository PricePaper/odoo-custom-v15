odoo.define('theme_clarico_vega.vertical_menu', function(require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.vertical_menu = publicWidget.Widget.extend({
        selector: ".te_bar_icon",
        start: function () {
            var self = this;
            self.callVerticalMenu();
        },
        callVerticalMenu: function(){
            // Vertical menu toggle
            $('.te_bar_icon').on('click', function(e){
                if($('.menu_vertical_option').length){
                    $(".te_vertical_menu").addClass('te_open').show('slow');
                    $("#wrapwrap").addClass("te_menu_overlay");
                }
                if( $('.te_vertical_menu.te_open').length ){
                    $('header#top').css('z-index','99');
                }
            });
            $(document).keyup(function(e) {
                 if (e.keyCode == 27) {
                   if ($(".te_vertical_menu").hasClass("te_open")) {
                        $(".te_vertical_menu").removeClass("te_open");
                        $("#wrapwrap").removeClass("te_menu_overlay");
                   }
                 }
            });
            $('.te_menu_icon_close').click(function(){
                $(".te_vertical_menu").removeClass("te_open");
                $("#wrapwrap").removeClass("te_menu_overlay");
                if( $('.te_vertical_menu').length ){
                    $('header#top').css('z-index','1030');
                }
            });

            // Vertical menu position
            var $h_menu = $("#oe_main_menu_navbar").height();
            if ($h_menu){
                $(".te_vertical_menu").css({top:$h_menu + 0, bottom: 0, left: 0, position:'fixed', 'z-index':9999});
            }
        },
    });

    $(document).mouseup(function(e)
    {
        var container = $(".te_vertical_menu");
        var edit_button = $(e.target.parentElement).attr('id');
        /* if the target of the click isn't the container nor a descendant of the container */
        if (!container.is(e.target) && container.has(e.target).length === 0 && edit_button != "edit-page-menu"){
            container.removeClass("te_open");
            $("#wrapwrap").removeClass("te_menu_overlay");
        }
    
    });
});
