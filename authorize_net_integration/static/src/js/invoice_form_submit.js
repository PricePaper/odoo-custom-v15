odoo.define('authorize_net_integration.submit', function (require) {
"use strict";
    $(document).ready(function() {
    $('#online_payment').one('submit',function(){
                $(this).find('input[type="submit"]').attr('disabled','disabled');

    });

    });

});