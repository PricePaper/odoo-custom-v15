odoo.define('accounting_extension.payment_info', function (require) {
"use strict";

var AccountPayment = require('account.payment');
var AbstractField = require('web.AbstractField');

 AccountPayment.ShowPaymentLineWidget.include({
    events: _.extend(AccountPayment.ShowPaymentLineWidget.prototype.events, {
        'click .js_payment_un_reconcile': '_onUnReconcileEntry',
    }),

    /**
     * @private
     * @override
     * @param {MouseEvent} event
     */
    _onUnReconcileEntry: function (event) {
        event.stopPropagation();
        event.preventDefault();
        var self = this;
        var paymentId = parseInt($(event.target).attr('payment-id')) || false;
        if (paymentId !== undefined && !isNaN(paymentId)){
            this._rpc({
                model: 'account.move.line',
                method: 'remove_active_discount',
                args: [paymentId, {'invoice_id': this.res_id}]
            }).then(function () {
                self.trigger_up('reload');
            });
        }
    },
});

});
