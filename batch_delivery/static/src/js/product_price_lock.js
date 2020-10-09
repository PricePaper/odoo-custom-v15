odoo.define('batch_delivery.price_lock', function (require) {
"use strict";

var AbstractField = require('web.AbstractField');
var core = require('web.core');
var field_registry = require('web.field_registry');
var field_utils = require('web.field_utils');

var QWeb = core.qweb;


var PriceLock = AbstractField.extend({
    events: _.extend({
        'click .js_price_lock': '_openPriceList',
    }, AbstractField.prototype.events),
    supportedFieldTypes: ['char'],


    isSet: function() {
        return true;
    },

    _render: function() {
        var self = this;
        var info = JSON.parse(this.value);
        if (!info) {
            this.$el.html('');
            return;
        }
        this.$el.html(QWeb.render('ShowPriceLockInfo', {
            title: info.title,
            form: info.record
        }));
    },

    _openPriceList: function (event) {
        event.stopPropagation();
        event.preventDefault();
        var self = this;
        var priceFormId = parseInt($(event.target).attr('price-form'));
        this.do_action({
            name: 'Customer Product Price',
            type: 'ir.actions.act_window',
            res_model: 'customer.product.price',
            views: [[false, 'form']],
            res_id: priceFormId,
            target:'new',
            flags:{mode:'readonly'}
            },
        );
    },

});

field_registry.add('price_lock', PriceLock);

return {
    ShowPriceLock: PriceLock
};
    
});
