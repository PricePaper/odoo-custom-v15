odoo.define('quick_create_disbale.many2one_quick_create_disbale', function (require) {
"use strict";

var relationField = require('web.relational_fields').FieldMany2One;

relationField.include({
  init: function (parent, name, record, options) {
        this._super.apply(this, arguments);
        this.can_create = false;
        }
     });
});
