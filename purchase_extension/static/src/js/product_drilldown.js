odoo.define('purchase_extension.product_drilldown', function (require) {
"use strict";

var field_registry = require('web.field_registry');
var FieldMany2One = require('web.relational_fields').FieldMany2One;


var ExternalDrillDown = FieldMany2One.extend({

    init: function (parent, name, record, options) {
        this._super.apply(this, arguments);
        this.limit = 7;;
    },

   _onClick: function (event) {
        var self = this;

        event.preventDefault();
        event.stopPropagation();

        if (this.mode === 'readonly'){
            self._onExternalButtonClick();
        }
    },

});

field_registry.add('product_external_drilldown', ExternalDrillDown);

return ExternalDrillDown;
});
