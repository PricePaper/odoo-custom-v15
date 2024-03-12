odoo.define('portal_enhancements.common', function (require) {
    'use strict';
    var core = require('web.core');
    const publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');

    publicWidget.registry.CompanySwithch = publicWidget.Widget.extend({
        selector: '.switch_company_wrap',
        events: {
            'click button.switch_company': '_onCompanySwithch',

        },
        _onCompanySwithch: function (ev) {
            var selected_company = $("select[name='company_switch']").val()
            console.log('hello')
            ajax.jsonRpc('/set/company', 'call', { 'company_id': selected_company }).then(function (result) {
                if (result.status) {
                    if (result.url) {
                        location.replace(result.url)
                    }
                    else {

                        location.replace("/my")
                    }
                }
            })
        }

    })



})

