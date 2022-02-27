odoo.define('account_batch_payment_extension.create', function (require) {
"use strict";

var core = require('web.core');
var LineRenderer = require('account.ReconciliationRenderer').LineRenderer;

var _t = core._t;

return LineRenderer.include({

      update: function (state) {
            var _super = this._super.bind(this);
            if (state.createForm) {
                var self = this;
                var label = state.createForm.name;
                var account = state.createForm.account_id;

                if (label == 'DEPOSIT_RETURN' && account) {
                    return self._rpc({
                        model: 'account.account',
                        method: 'search_read',
                        domain: [['id', '=', account.id]],
                        fields: ['internal_type'],
                        }).then(function (rec) {
                            if(rec[0].internal_type != "receivable") {
                                self.displayNotification({ title: _t('Alert!!'), message: _t('DEPOSIT RETURN write-off Account should be receivable account.'), sticky: true, type: 'danger' });
                                return;
                            }
                            return _super(state);
                    });
                }
            }
            return _super(state);
      }
    });
});
