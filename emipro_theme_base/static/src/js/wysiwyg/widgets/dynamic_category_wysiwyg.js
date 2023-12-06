odoo.define('emipro_theme_base.dynamic_category_wysiwyg', function (require) {
'use strict';
    const LinkDialog = require('wysiwyg.widgets.LinkDialog')
    const Dialog = require('web.Dialog');
    const Link = require('wysiwyg.widgets.Link');

    LinkDialog.include({
        // Menu data save button click method
        save: function () {
            var data = this.linkWidget._getData();
            var getUpdateData = this.linkWidget.data;
            if (data != null) {
                data.is_dynamic_menu = this.$('input[name="is_dynamic_menu"]').prop('checked') || false;
                data.menu_label_text = this.$('input[name="menu_label_text"]').val();
                data.menu_label_text_color = this.$('input[name="menu_label_text_color"]').val();
                data.is_highlight_menu = this.$('input[name="is_highlight_menu"]').prop('checked') || false;
                getUpdateData.is_dynamic_menu = data.is_dynamic_menu;
                getUpdateData.menu_label_text = data.menu_label_text;
                getUpdateData.menu_label_text_color = data.menu_label_text_color;
                getUpdateData.is_highlight_menu = data.is_highlight_menu;
            }
            return this._super(...arguments);
        },
    });

});

odoo.define('wysiwyg.widgets.LinkEpt', function (require) {
    const LinkTools = require('wysiwyg.widgets.LinkTools');
    LinkTools.include({
        /*** @override */
        focusUrl() {
            if(this.el) {
                this._super();
            }
        }
    });
})
