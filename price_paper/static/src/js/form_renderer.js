odoo.define('sale_confirm_button.FormRenderer', function (require) {
    "use strict";

    var FormController = require('web.FormController');


    return FormController.include({
        _onSave: function (ev) {
            var self = this;
            this._super.apply(this, arguments);
            console.log(self);
            if (self.modelName == "sale.order" && !self.renderer.state.data.id && !self.initialState.data.storage_contract) {
                if(confirm("Do you want to Confirm this Sale Order?")) {
                    $("button[name='action_confirm'].btn-secondary").trigger('click');
                }
            }
        },
    });

});
