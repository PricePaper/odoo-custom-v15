odoo.define('authorize_net_integration.screen_invoices_id', function (require) {
                    "use strict";
// var alert=require('authorize_net_integration.alert');
 var core = require('web.core');
 var _t = core._t;
var Dialog = require('web.Dialog');

 window.onload = function() {
        $('.online_payment').each(function(){
        try{
        var isMobile = /iPhone|iPod|Android/i.test(navigator.userAgent);
        if (isMobile){
        $("#app_view").css("display", "block");
        }
        $('.default_invoice').closest('tr').toggleClass("highlight", this.checked);
        if ($("#error_m").prop('checked')){

            var value=JSON.parse(localStorage.getItem('selected_ids'));
            window.localStorage.setItem('selected_ids','');
             var array = JSON.parse("[" + value + "]");
             $('input[type=checkbox]').map(function(i, e) {
                    var a=$(e).val();
                    a=parseInt(a);
                    if (array.indexOf(a)>-1)
                    {$(e).trigger('click');}

                });
             var checked = JSON.parse(localStorage.getItem('other_check'));
             localStorage.setItem('other_check',false);
            if (checked == true) {
                $("#other_check").trigger('click');
                var reason=window.localStorage.getItem('description');
                window.localStorage.setItem('description','');
                 var extra_amount=JSON.parse(window.localStorage.getItem('extra'));
                 window.localStorage.setItem('extra','');
                 $('#extra_content_reason').val(reason);
                  $("input[name = 'extra_amount']").val(extra_amount)
                  $('#extra_payments').trigger('keyup');

            }
            }
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
        }
        catch(err){}
        });


        };
     $(document).ready(function() {


     $('.online_payment').each(function(){

        $('.extra_payments').hide();
        var value=0;
        var amount=parseFloat(document.getElementById("invoice_amount").value);
        amount=amount-parseFloat(document.getElementById("credit_amount").value);
        $(".invoices_open_boxs").click(function() {
            if (this.checked) {
                   var value =  $(this).data("attribute_value_ids");
                   var current_amount=parseFloat(document.getElementById("amount").value)+parseFloat(value)
                   document.getElementById("amount").value=current_amount.toFixed(2);
                   amount= parseFloat(document.getElementById("amount").value);
                   var invoice=parseFloat(document.getElementById("invoice_amount").value)+parseFloat(value);
                   document.getElementById("invoice_amount").value=invoice.toFixed(2);
             }
             else{
                  var value =$(this).data("attribute_value_ids");
                  var current_amount=parseFloat(document.getElementById("amount").value)-parseFloat(value);
                  if (current_amount<=0){
                  Dialog.alert(this, _t("Total payment amount must be positive.Adjust your credit memo first to continue with this action "),{
                  title: _t("Warning"),});
//                    alert.ed_alert('Warning','Total payment amount must be positive.Adjust your credit memo first to continue with this action.','Ok','', 'GoToAssetList',null);
                  $(this).prop('checked',true);
                  }
                  else{
                  document.getElementById("amount").value=current_amount.toFixed(2);
                  amount= parseFloat(document.getElementById("amount").value);
                  var invoice=parseFloat(document.getElementById("invoice_amount").value)-parseFloat(value);
                  document.getElementById("invoice_amount").value=invoice.toFixed(2);
                  }


             }
             $('#amount').trigger('change');

        });

        $(".extra_amount").click(function() {
                 if (this.checked) {
                     $('.extra_payments').show();
                     $('#extra_content_reason').show();
                     $(".extra_payments").keyup(function(){
                          var value=document.getElementById("extra_payments").value;
                          if (value!=""){
                                amount=parseFloat(document.getElementById("invoice_amount").value)-parseFloat(document.getElementById("credit_amount").value);
                                var cur_amount=amount+parseFloat(value);
                                cur_amount=cur_amount.toFixed(2);
                                document.getElementById("amount").value=cur_amount;
                                $('#amount').trigger('change');
                            }
                        else{
                        amount=parseFloat(document.getElementById("invoice_amount").value)-parseFloat(document.getElementById("credit_amount").value);
                        document.getElementById("amount").value=amount.toFixed(2);
                        $('#amount').trigger('change');

                            }
                      });
                 }
                 else{
                     $('.extra_payments').hide();
                     $('#extra_content_reason').hide();
                     document.getElementById("extra_payments").value='';
                     document.getElementById("extra_content_reason").value='';
                     $(".extra_payments").trigger('keyup');
//                     document.getElementById("amount").value=amount.toFixed(2);
//                     $('#amount').trigger('change');

                 }

        });
        $(".mySearch").keyup(function(){
                var input, filter, table, tr, td, i,k;
                k=$('.search_by').val();
                input = document.getElementById("myInput");
                filter = input.value.toUpperCase();
                table = document.getElementById("myTable");
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

        $('.search_by').on('change',function(){
        $('.mySearch').trigger('keyup');
        })

       $("input[type='checkbox']").on('change', function() {
            $(this).closest('tr').toggleClass("highlight", this.checked);
        });

        $('.table-invoice tr').on( "click", function( event ) {
            if (event.target.type !== 'checkbox') {
                $(':checkbox', this).trigger('click');
            }
        });
        $("#online_payment").submit(function () {
                window.localStorage.setItem('extra',$("input[name = 'extra_amount']").val());
                window.localStorage.setItem('description',$('#extra_content_reason').val());
                var checkbox = document.getElementById('other_check');
                if(document.getElementById('other_check').checked) {
                    localStorage.setItem('other_check', true);
                    }
                    var selected_ids=[]
                    $('#myTable').find('input[type="checkbox"]:checked').each(function () {
                    selected_ids.push($(this).val());
                    localStorage.setItem("selected_ids", JSON.stringify(selected_ids));

                });
                $('#myCredit').find('input[type="checkbox"]:checked').each(function () {
                    selected_ids.push($(this).val());
                    localStorage.setItem("selected_ids", JSON.stringify(selected_ids));

                });
            });
            $('#myTable th').each(function(col) {
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
      var arrData = $('#myTable').find('tbody >tr:has(td)').get();
      arrData.sort(function(a, b) {
        var val1 = $(a).children('td').eq(col).text().toUpperCase();
        var val2 = $(b).children('td').eq(col).text().toUpperCase();
        if($.isNumeric(val1) && $.isNumeric(val2))
        return sortOrder == 1 ? val1-val2 : val2-val1;
        else
           return (val1 < val2) ? -sortOrder : (val1 > val2) ? sortOrder : 0;
      });
      $.each(arrData, function(index, row) {
        $('#myTable tbody').append(row);
      });
    });
  });


});
    });

});