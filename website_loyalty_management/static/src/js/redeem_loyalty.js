odoo.define('website_loyalty_management.redeem_loyalty', function (require) {
    'use strict';

    var ajax = require('web.ajax');

    $(document).ready(function () {
        $('#redeem_loyalty_button').on('click', function () {
            $('#redeem_loyalty_modal').modal('show');
        });

        $('#submit_redeem_loyalty').on('click', function () {
            var order_id = $('input[name="order_id"]').val();
            var points_to_redeem = $('#points_to_redeem').val();

            if (points_to_redeem && order_id) {
                ajax.jsonRpc('/shop/redeem_loyalty', 'call', {
                    order_id: parseInt(order_id),
                    points_to_redeem: parseInt(points_to_redeem)
                }).then(function (result) {
                console.log(result)
                    if (result.status === 'success') {
                        alert(result.message);
                        location.reload();
                    } else {
                        alert(result.message);
                    }
                    $('#redeem_loyalty_modal').modal('hide');
                });
            }
        });
    });
});
