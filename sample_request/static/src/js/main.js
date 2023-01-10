odoo.define('sample_request.product', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var _t = core._t;
    publicWidget.registry.websiteSaleCategory = publicWidget.Widget.extend({
        selector: '#product_detail',
        events: {
            'click .sample_request': '_onSampleRequest',
            
        },
        _onSampleRequest:function(ev){
            var self = this
            var product_id = $(ev.currentTarget).parents('div#product_details').find('input[name=product_id]').val()
            this._rpc({
                route: '/sample/request/update',
                params: {
                    product_id: product_id,
                }
            }).then(function (res) {
                if (!res.error){
                    window.location.href='/sample/request'
                }
                else{
                    $(self.$target).find('.sample_erorr').html(res.error).removeClass('d-none').addClass('text-danger')
                }
            });
        }

    })
})