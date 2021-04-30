odoo.define('authorize_net_integration.payment_methods', function(require){
"use_strict";

$(document).ready(function() {
        $('#selected_p_method').attr('value','card');
        var processing_fee = $('#handling_fee').val();
        var total_production_cost = $('#production_total').val();
        $(".payment_card_select").css("color", "green");
        $('.cheque_payment_body').hide();
        var action = $("#online_payment").attr('action');
        $('.payment_card_select').on('click', function(){
        $('#handling_fee').val(processing_fee);
        $('#amount').trigger('change');
        $('#production_total').attr('value',parseFloat(total_production_cost));
        $(".payment_card_select").css("color", "green");
        $(".payment_check_select").css("color", "#4e4e4e");
        $('.hide_processing').show();
                $("#online_payment").attr('action', action);
                $('.card_payment_body').show();
                $('.cheque_payment_body').hide();
                $('.surcharge_box').show();
                $('#cardNumber').attr('required', true);
                $('#cvCode').attr('required', true);
                $('#expiry_month').attr('required', true);
                $('#account_number').attr('required', false);
                $('#account_name').attr('required', false);
                $('#routing_number').attr('required', false);
//                $('#eCheck_type').attr('required', false);
//                $('#account_type').attr('required', false);
                $('#bank_name').attr('required', false);
                $('#selected_p_method').prop('checked',true);
                $('#selected_p_method').attr('value','card');

            });
            $('.payment_check_select').on('click', function(){
                $('#handling_fee').val('0.0');
                var value= parseFloat($('#amount').val());
//                 $('#final_amount').val(value.toFixed(2));
                $('#selected_p_method').prop('checked',false);
                $('#selected_p_method').attr('value','check');
                $('#amount').trigger('change');
//                $('#production_total').attr('value',parseFloat(total_production_cost)-parseFloat(processing_fee));
                $('.hide_processing').hide();
                $("#online_payment").attr('action', '/eCheque_payment');
                $('.card_payment_body').hide();
                $('.surcharge_box').hide();
                $('.cheque_payment_body').show();
                $(".payment_check_select").css("color", "green");
                $(".payment_card_select").css("color", "#4e4e4e");

                $('#cardNumber').attr('required', false);
                $('#cvCode').attr('required', false);
                $('#expiry_month').attr('required', false);
                $('#account_number').attr('required', true);
                $('#account_name').attr('required', true);
                $('#routing_number').attr('required', true);
//                $('#eCheck_type').attr('required', true);
//                $('#account_type').attr('required', true);
                $('#bank_name').attr('required', true);


        });

});


});