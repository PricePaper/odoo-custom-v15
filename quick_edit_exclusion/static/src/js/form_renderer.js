odoo.define('quick_edit_exclusion.FormRenderer', function (require) {
    "use strict";

    var FormRenderer = require('web.FormRenderer');

    return FormRenderer.include({
        _onQuickEdit: function (ev) {
            if (this.mode == 'readonly') {
                ev.stopPropagation();
            } else {
                this._super.apply(this, arguments);
            }
        },
    })

});
