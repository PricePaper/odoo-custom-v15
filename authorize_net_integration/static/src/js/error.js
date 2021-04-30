odoo.define('authorize_net_integration.errors', function (require) {
"use strict";
 $(document).ready( function() {
 $('.online_payment').each(function(){

if ($("#error_m").prop('checked')){
 loadPopupBox();
        $('#popupBoxClose').click( function() {
            unloadPopupBox();
        });

        $('#container').click( function() {
            unloadPopupBox();
        });

        function unloadPopupBox() {    // TO Unload the Popupbox
            $('#popup_box').fadeOut("slow");
            $("#container").css({ // this is just for style
                "opacity": "1"
            });
        }
//
        function loadPopupBox() {    // To Load the Popupbox
            var counter = 20;
            var id;
            $('#popup_box').fadeIn("slow");
            $("#container").css({ // this is just for style
                "opacity": "0.3"
            });

            id = setInterval(function() {
                counter--;
                if(counter < 0) {
                    clearInterval(id);

                    unloadPopupBox();
                } else {
//                    $("#countDown").text("it closed  after " + counter.toString() + " seconds.");
                }
            }, 1000);

        }
}
});

    });

});
