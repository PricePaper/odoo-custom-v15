odoo.define('automatic.backup', function (require) {
    "use strict";

    var basic_fields = require('web.basic_fields');

    basic_fields.UrlWidget.include({
        _renderReadonly: function () {
            this.$el.text(this.attrs.text || this.value)
                .addClass('o_form_uri o_text_overflow')
                .attr('href', this.value)
                .attr('target', '_blank');
        }
    });

});