odoo.define('authorize_net_integration.credit_memo', function (require) {
                    "use strict";
//                    var ed_alert = require('authorize_net_integration.alert');
                    var core = require('web.core');
                    var _t = core._t;
                    var Dialog = require('web.Dialog');

           $(document).ready(function() {

            $('.online_payment').each(function(){
//                        $('#invoices_view').hide();
                        $('.credit_list').hide();
                        $('#cm a').click(function(){
                                $('#ed_app_switcher').hide();
                                $('.mySearch').val('');
                                $('.mySearch').trigger('keyup');
                                $('#cm').hide();
                                $('#invoices_view').show();
                                $('.invoice_list').hide();
                                $('.credit_list').show();
//                                $('#my_cart').hide();
                        });
                        $('#invoices_view ').click(function(){
                                $('#ed_app_switcher').hide();
                                $('#my_cart').show();
                                $('.mySearch').val('');
                                $('.mySearch').trigger('keyup');
                                $('#cm').show();
//                                $('#invoices_view').hide();
                                $('.invoice_list').show();
                                $('.credit_list').hide();
                        });

                       $('#amount').change(function(){
                            if ($('#selected_p_method').val()=='card'){
                           $('#handling_fee').val((parseFloat($('#amount').val())*parseFloat($('#surcharge_percentage').val())/100).toFixed(2));
                           }
                            var value= parseFloat($('#amount').val())+parseFloat($('#handling_fee').val());
                            $('#final_amount').val(value.toFixed(2));
                            });



                        $(".invoices_credit_boxs").click(function() {
                                if (this.checked) {
                                       var value =  $(this).data("attribute_credit_ids");
                                       var current_amount=parseFloat(document.getElementById("amount").value)-parseFloat(value);
                                       var credit_value=parseFloat(document.getElementById("credit_amount").value)+parseFloat(value);
                                       if(credit_value>=parseFloat(document.getElementById("invoice_amount").value)){
                                       Dialog.alert(this, _t("Total Payment Amount Must be strictly positive"),{
                                       title: _t("Warning"),
                                       });
//                                       $('.alert-info').html(_t('Your changes have not been saved, try again later.')).removeClass('alert-info').addClass('alert-warning');
//                                         ed_alert.ed_alert('Warning','Total Payment Amount Must be strictly positive.','Ok','', 'GoToAssetList',null);
                                        $(this).prop('checked',false);
                                       }
                                       else{
                                       document.getElementById("amount").value=current_amount.toFixed(2);
                                       document.getElementById("credit_amount").value=credit_value.toFixed(2);

                                       }

                                 }
                                 else{
                                      var value =$(this).data("attribute_credit_ids");
                                      var current_amount=parseFloat(document.getElementById("amount").value)+parseFloat(value);
                                      document.getElementById("amount").value=current_amount.toFixed(2);
                                      var credit_value=parseFloat(document.getElementById("credit_amount").value)-parseFloat(value);
                                      document.getElementById("credit_amount").value=credit_value.toFixed(2);

                                 }
                                 $('#amount').trigger('change');

                        });
                        $(".mySearch").keyup(function(){
                            var input, filter, table, tr, td, i,k;
                            k=$('.search_by').val();
                            input = document.getElementById("myInput");
                            filter = input.value.toUpperCase();
                            table = document.getElementById("myCredit");
                            tr = table.getElementsByTagName("tr");
                            for (i = 0; i <tr.length; i++) {
                                td = tr[i].getElementsByTagName("td")[k];
                                if (td) {
                                      if ($(td).text().toUpperCase().indexOf(filter) > -1) {
                                            tr[i].style.display = "";
                                      }
                                      else {
                                            tr[i].style.display = "none";
                                      }
                                }
                                    }
                            });
                            $('#myCredit th').each(function(col) {
                                    $(this).hover(
                                        function() { $(this).addClass('sort-focus'); },
                                        function() { $(this).removeClass('sort-focus'); }
                                    );
                                    var sortOrder;
                                    $(this).click(function() {
                                    if ($(this).is('.asc')) {
                                      $(this).removeClass('asc');
                                        $(this).addClass('desc selected-sort');
                                        sortOrder = -1;
                                        }
                                     else {
                                        $(this).addClass('asc selected-sort');
                                        $(this).removeClass('desc');
                                        sortOrder = 1;
                                    }
                                      $(this).siblings().removeClass('asc selected-sort');
                                      $(this).siblings().removeClass('desc selected-sort');
                                      var arrData = $('#myCredit').find('tbody >tr:has(td)').get();
                                    arrData.sort(function(a, b) {
                                        var val1 = $(a).children('td').eq(col).text().toUpperCase();
                                        var val2 = $(b).children('td').eq(col).text().toUpperCase();
                                        if($.isNumeric(val1) && $.isNumeric(val2))
                                        return sortOrder == 1 ? val1-val2 : val2-val1;
                                        else
                                           return (val1 < val2) ? -sortOrder : (val1 > val2) ? sortOrder : 0;
                                  });
                              $.each(arrData, function(index, row) {
                                $('#myCredit tbody').append(row);
                              });
                            });
                     });



             });

            });
});