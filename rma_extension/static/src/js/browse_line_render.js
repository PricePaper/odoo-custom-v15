odoo.define('rma_extension.payment_info', function (require) {
"use strict";

var ListRenderer = require('web.ListRenderer');

ListRenderer.include({

    _renderRow: function (record, index) {
        var $row = this._super.apply(this, arguments);
        if (this.addTrashIcon) {
            var $icon = this.isMany2Many ?
                            $('<button>', {class: 'fa fa-times', name: 'unlink', 'aria-label': _t('Unlink row ') + (index+1)}) :
                            $('<button>', {class: 'fa fa-trash-o', name: 'delete', 'aria-label': _t('Delete row ') + (index+1)});
            var $td = $('<td>', {class: 'o_list_record_remove'}).append($icon);
            $row.append($td);
        }

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

     _onCellClick: function (event) {


        if (!this._isEditable() || $(event.target).prop('special_click')) {
            return;
        }

       var $td = $(event.currentTarget);
       var $tr = $td.parent();
       var $checkbox = $tr.find('input[type=checkbox]');

       if (!$checkbox.prop('checked')){
            $checkbox.trigger('click');
            if($checkbox.prop('checked')){
                $tr.css('background-color', '#faebd7');
            }
        }

        var rowIndex = this.$('.o_data_row').index($tr);
        var fieldIndex = Math.max($tr.find('.o_data_cell').not('.o_list_button').index($td), 0);
        this._selectCell(rowIndex, fieldIndex, {event: event});
    },
});

});
