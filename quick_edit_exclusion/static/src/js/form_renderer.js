odoo.define('quick_edit_exclusion.FormRenderer', function (require) {
    "use strict";

    var FormRenderer = require('web.FormRenderer');

    FormRenderer.include({

        init: function (parent, state, params) {
            this._super.apply(this, arguments);
            const self = this;
            this.getSession().user_has_group('quick_edit_exclusion.group_edit_permission').then(function(has_group) {
                self.is_group = has_group});}});

    return FormRenderer.include({
        _onQuickEdit: function (ev) {
             if (this.mode == 'readonly' && !this.is_group)
                {ev.stopPropagation();
            }
            else {
                this._super.apply(this, arguments);
            }
        },
    })

});