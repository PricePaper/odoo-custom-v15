odoo.define('authorize_net_integration.invoice_cart', function (require) {
"use strict";

//var base = require('web_editor.base');
require('web.dom_ready');
var core = require('web.core');
var _t = core._t;
$('.online_payment').each(function(){
var shopping_cart_link = $('#invoice_amount');
var shopping_cart_link_counter;
shopping_cart_link.popover({
    trigger: 'manual',
    animation: true,
    html: true,
    title: function () {
        return _t("Invoices");
    },
    container: 'body',
    placement: 'auto',
    template: '<div class="popover mycart-popover" role="tooltip"><div class="arrow"></div><h3 class="popover-title"></h3><div class="popover-content"></div></div>'
}).on("mouseenter",function () {
        var count = $('#myTable .invoices_open_boxs:checked').length;
        var data="<div><h5>Number of invoices included : "+(parseFloat(count)+1)+"</h5><hr></hr>click to view the included invoices</div>"
        $(this).data("bs.popover").options.content =data;
         $(this).popover('show');
}).on("mouseleave", function () {
    $(this).popover('hide');

});

var credit_link = $('#credit_amount');
var shopping_cart_link_counter;
credit_link.popover({
    trigger: 'manual',
    animation: true,
    html: true,
    title: function () {
        return _t("Credit Memo");
    },
    container: 'body',
    placement: 'auto',
    template: '<div class="popover mycart-popover" role="tooltip"><div class="arrow"></div><h3 class="popover-title"></h3><div class="popover-content"></div></div>'
}).on("mouseenter",function () {
        var count = $('#myCredit .invoices_credit_boxs:checked').length;
        var data="<div><h5>Number of credit memo included : "+(parseFloat(count))+"</h5><hr></hr>click to view the included CM</div>"
        $(this).data("bs.popover").options.content =data;
         $(this).popover('show');


}).on("mouseleave", function () {
    $(this).popover('hide');

});
});

});