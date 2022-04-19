odoo.define('quick_create_disbale.many2one_quick_create_disbale', function (require) {
"use strict";

var relationField = require('web.relational_fields').FieldMany2One;

relationField.include({
  init: function (parent, name, record, options) {
        this._super.apply(this, arguments);
        const self = this;
        this.getSession().user_has_group('quick_create_disable.group_create_permission').then(function(has_group) {
            if(!has_group){
                self.can_create = false;
            }
            else{
                self.can_create = true;
            }
        });
        }
     });
});
