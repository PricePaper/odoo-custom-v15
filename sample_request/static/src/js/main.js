odoo.define('sample_request.product', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    $.blockUI.defaults.css.border = '0';
    $.blockUI.defaults.css["background-color"] = '';
    $.blockUI.defaults.overlayCSS["opacity"] = '0.9';
    var core = require('web.core');
    var _t = core._t;

    publicWidget.registry.SampleCart = publicWidget.Widget.extend({
        selector: '.sample_request_cart',
        events: {
            'click .process_request': '_processRequest',
            'click .delete-sample':'_deleteSample'
        },
        _deleteSample:function(ev){
            var line_id =  $(ev.currentTarget).attr('data-id')
            ev.preventDefault()
            ev.stopPropagation();
            var $self = this
            var msg = ("We are processing your request, please wait ...");
            $.blockUI({
                'message': '<h2 class="text-white"><img src="/web/static/img/spin.png" class="fa-pulse"/>' +
                    '    <br />' + msg +
                    '</h2>'
            });

            $self._rpc({
                model: 'sample.request.line',
                method: 'unlink',
                args: [[parseInt(line_id)]],
            }).then(function () {
                window.location.reload();


            });

        },
        _processRequest: function (ev) {
            var href = $(ev.currentTarget).attr('href')
            ev.preventDefault()
            ev.stopPropagation();
            var $self = this
            var msg = ("We are processing your request, please wait ...");
            $.blockUI({
                'message': '<h2 class="text-white"><img src="/web/static/img/spin.png" class="fa-pulse"/>' +
                    '    <br />' + msg +
                    '</h2>'
            });
            $('input[name=note_line]').each(function () {
                var line_id = $(this).attr('data-line')
                if ($(this).val()) {
                    $self._rpc({
                        model: 'sample.request.line',
                        method: 'write',
                        args: [[parseInt(line_id)], { 'note': $(this).val() }],
                    }).then(function () {



                    });
                }
            }).promise().done(function () {
                window.location = href
            })

        }
    })
    publicWidget.registry.SampleAdd = publicWidget.Widget.extend({
        selector: '#product_detail',
        events: {
            'click .sample_request': '_onSampleRequest',

        },
        _onSampleRequest: function (ev) {
            var self = this
            var product_id = $(ev.currentTarget).parents('div#product_details').find('input[name=product_id]').val()
            this._rpc({
                route: '/sample/request/update',
                params: {
                    product_id: product_id,
                }
            }).then(function (res) {
                if (!res.error) {
                    window.location.href = '/sample/request'
                }
                else {
                    $(self.$target).find('.sample_erorr').html(res.error).removeClass('d-none').addClass('text-danger')
                }
            });
        }

    })
})
