odoo.define('quick_edit_exclusion.ListRenderer', function (require) {
    "use strict";

    const ListRenderer = require('web.ListRenderer');

    ListRenderer.include({
        init: function (parent, state, params) {
            params.no_open = false;
            this._super.apply(this, arguments);
            // const parm = params
            // this.getSession().user_has_group('quick_edit_exclusion.group_edit_permission').then(function(has_group) {
            //     if (!has_group){
            //          parm.no_open = false;
            //     }
            // });
        }
    });

});
