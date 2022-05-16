odoo.define('batch_payment_match.reconciliation', function (require) {
    "use strict";

    var ReconciliationRenderer = require('account.ReconciliationRenderer');


    var Renderer = {
        update: function (state) {
            if (state.relevant_payments.length) {
                state.relevant_payments.forEach(function (payment) {
                    if (payment.amount == state.balance.amount) {
                        payment.batch_amount_match = true;
                    } else {
                        payment.batch_amount_match = false;
                    }
                });
            }
            this._super(state);
        },
    };

    ReconciliationRenderer.LineRenderer.include(Renderer);
    ReconciliationRenderer.ManualLineRenderer.include(Renderer);

});
