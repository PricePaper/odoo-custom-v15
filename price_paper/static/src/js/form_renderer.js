odoo.define('price_paper.FormRenderer', function (require) {
    "use strict";

    const FormController = require('web.FormController');


    FormController.include({
        _onSave: function (ev) {

            var self = this;
            this._super.apply(this, arguments);

            if (self.modelName == "sale.order" && ['draft', 'sent'].includes(self.renderer.state.data.state) && !self.initialState.data.storage_contract) {
                if(confirm("Do you want to Confirm this Sale Order?")) {
                    $("button[name='action_confirm'].btn-secondary").trigger('click');
                }
            }
        },
    });

});
