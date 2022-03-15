odoo.define('quick_edit_exclusion.ListRenderer', function (require) {
    "use strict";

    const ListRenderer = require('web.ListRenderer');


    ListRenderer.include({
        init: function (parent, state, params) {
            params.no_open = false;
            this._super.apply(this, arguments);
        }
    });

});
