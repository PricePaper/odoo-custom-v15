odoo.define('authorize_net_integration.my_cart_view', function (require) {
"use strict";
 $(document).ready(function() {
$('#my_cart').click(function(){
$('#ed_app_switcher').hide();
 $("table tr").has("input[type='checkbox']:not(:checked)").hide();
 $('#invoices_view').show();
// $('#my_cart').hide();
 $('.credit_list').hide();
$('.invoice_list').show();


});
$( "#invoice_amount" ).click(function() {
  $('#my_cart').trigger('click');
});
$( "#credit_amount" ).click(function() {
//    $('#my_cart').hide();
$('#ed_app_switcher').hide();
  $("#myCredit tr").has("input[type='checkbox']:not(:checked)").hide();
  $('#invoices_view').show();
  $('.invoice_list').hide();
$('.credit_list').show();
});

$('#my_cart_cm').click(function(){
$( "#credit_amount" ).trigger('click');
});

$('.credit_memo_avail').click(function(){
    $('#cm a').trigger('click');
});

$('#app_view').click(function(){
$('.invoice_list').hide();
$('.credit_list').hide();
$("#ed_app_switcher").show();
});


});



});