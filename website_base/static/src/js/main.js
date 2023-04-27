odoo.define('website_base.product_uom', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var _t = core._t;
    var ajax = require('web.ajax')
    $.blockUI.defaults.css.border = '0';
    $.blockUI.defaults.css["background-color"] = '';
    $.blockUI.defaults.overlayCSS["opacity"] = '0.9';
    // ajax.jsonRpc('/hover/color', 'call', params).then(function (data) {

        // $.blockUI({
        //     'message': '<h2 class="text-white"><img src="/web/static/img/spin.png" class="fa-pulse"/>' +
        //         '    <br />' + msg +
        //         '</h2>'
        // });



        publicWidget.registry.productUom = publicWidget.Widget.extend({
            selector: '#product_details',
            events: {

                'change #UomProduct': "_onUomChange"

            },
            _onUomChange: function (ev) {
                var uom_id = $(ev.currentTarget).val()
                var self =  this 
                var $target = $(this.$target)
                var product_id = $("input[name='product_id']").val()
                var msg = "We are updating the Uom and price "
                $.blockUI({
                    'message': '<h2 class="text-white"><img src="/web/static/img/spin.png" class="fa-pulse"/>' +
                        '    <br />' + msg +
                        '</h2>'
                });
                var params = {'uom_id':uom_id,'product_id':product_id}
                ajax.jsonRpc('/get/uom/price', 'call', params).then(function (data) {
                    if (data){
                        $.unblockUI();
                        $target.find('.new_pice').find('.oe_currency_value').text(data.new_price)
                        // console.log(data)
                    }
                });

                // if($(ev.currentTarget).is(":checked")){
                //     $('.delivey_select').removeClass('d-none');
                // }
                // else{
                //     $('.delivey_select').addClass('d-none');
                // }
            },
            _genrateToken: function (ev) {
                Swal.fire('HELLO')
            }

        })
    })
// })