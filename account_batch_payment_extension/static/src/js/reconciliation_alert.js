odoo.define('account_batch_payment_extension.create', function (require) {
"use strict";
var Dialog = require('web.Dialog');
var core = require('web.core');
var LineRenderer = require('account.ReconciliationRenderer').LineRenderer;

var _t = core._t;

return LineRenderer.include({

      update: function (state) {
            if (state.createForm){
                var label = state.createForm.label;
                var account = state.createForm.account_id;
                if (label == 'DEPOSIT_RETURN' && account && account.display_name.indexOf("101200") == -1){
                    this.do_warn(_t("Alert!!"), 'Account should be receivable account.');
                    return;
                    }
                }
            this._super(state);
      }
    });
});
