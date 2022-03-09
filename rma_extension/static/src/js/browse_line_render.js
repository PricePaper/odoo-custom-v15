odoo.define('rma_extension.list_render', function (require) {
"use strict";

var ListRenderer = require('web.ListRenderer');

ListRenderer.include({

    _renderRow: function (record, index) {
        var $row = this._super.apply(this, arguments);

        if(record.model === 'browse.lines.source.line'){
            if(record.data.select){
                $row.css('background-color', '#faebd7');
            }
            else
            {
                $row.css('background-color', '#ffffff');
            }
        }
        return $row;
    },

//     _onCellClick: function (event) {
//       this._super(event);
//       if(this._isEditable() && this.arch.attrs.quick_selection === 'active'){
//            var $td = $(event.currentTarget);
//            var $tr = $td.parent();
//            var $checkbox = $tr.find('input[type=checkbox]');
//            if (!$checkbox.prop('checked')){
//                $checkbox.trigger('click');
//                if($checkbox.prop('checked')){
//                    $tr.css('background-color', '#faebd7');
//                }
//            }
//       }
//    },
});

});
