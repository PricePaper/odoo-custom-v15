odoo.define('theme_clarico_vega.s_editor_js', function(require) {
    'use strict';
    var SnippetEditor = require("web_editor.snippet.editor");

    SnippetEditor.SnippetEditor.include({
        /* To make the hotspot elements Draggable in Edit Mode */
        start: function() {
            var self = this;
            var def = this._super.apply(this, arguments);
            return def.then(() => {
                $('#ajax_cart_model_shop, #quick_view_model_shop, #ajax_cart_model_shop').modal('hide');
                $("body section.hotspot_element").each(function() {
                    $(this).draggable({
                        containment: 'parent',
                        opacity: 0.4,
                        scroll: false,
                        revertDuration: 200,
                        refreshPositions: true,
                        stop: function() {
                            var l = (100 * parseFloat($(this).position().left / parseFloat($(this).parent().width()))) + "%";
                            var t = (100 * parseFloat($(this).position().top / parseFloat($(this).parent().height()))) + "%";
                            $(this).css("left", l);
                            $(this).css("top", t);
                        }
                    })
                });
            })
        },
    });
});
