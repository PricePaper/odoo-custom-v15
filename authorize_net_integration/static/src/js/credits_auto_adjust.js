odoo.define('authorize_net_integration.auto_adjust', function (require) {
"use strict";
 $(document).ready( function() {
    $('.online_payment').each(function(){
        $('.auto_adjust').click(function(){
            var credit_list = [];
            $('#myCredit').find('input[type="checkbox"]:not(:checked)').each(function(){
                credit_list.push($(this));

                });
                    var list_credit =[]
                    var amount = $('#amount').val();
                 _.each(credit_list,function(credit){

                    var adjusted_amount = 0;
                    adjusted_amount =amount-parseInt($(credit).data('attribute_credit_ids'));
                    if (adjusted_amount>0){
                            amount =adjusted_amount
                            list_credit.push(credit);
//                        $("#credit_amount" ).trigger('click');
                    }



                });
                _.each(list_credit, function(obj){
                $(obj).trigger('click').change();
//

                });
                $('#cm a').trigger('click');





          });

    });

});

});
