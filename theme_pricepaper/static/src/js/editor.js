odoo.define('theme_pricepaper.editor', function (require) {
    'use strict';

    var core = require('web.core');
    const weSnippetEditor = require('web_editor.snippet.editor');
    weSnippetEditor.SnippetsMenu.include({
        _onSaveRequest: function (ev) {
            $('.home-contact-us').find('#captcha').remove()
            return this._super(...arguments);
        },
    })
});
