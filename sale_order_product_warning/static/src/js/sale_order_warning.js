odoo.define('sale_order_product_warning.sale_order_warning', function (require) {
"use strict";

var FormController = require('web.FormController');
var core = require('web.core');
var Dialog = require('web.Dialog');
var dialogs = require('web.view_dialogs');

var _t = core._t;
var qweb = core.qweb;

FormController.include({
    checkCanBeSaved: function (recordID) {
        var fieldNames = this.renderer.canBeSaved(recordID || this.handle);
        if (fieldNames.length) {
            return false;
        }
        return true;
    },
    /**
     * Called when the user wants to save the current record -> @see saveRecord
     *
     * @private
     * @param {MouseEvent} ev
     */
    _onSave: function (ev) {
        ev.stopPropagation(); // Prevent x2m lines to be auto-saved
        // this._disableButtons();
        var self = this;
        var modelName = this.modelName ? this.modelName : false;
        var record = this.model.get(this.handle, {raw: true});
        var data_changed = record ? record.data : false;
        var confirm = 'There is some duplicate product lines please check';
        var alert =  self.activeActions.alert;
        var canBeSaved = record && record.id ? self.checkCanBeSaved(record.id) : false;
        function saveAndExecuteAction () {
            ev.stopPropagation(); // Prevent x2m lines to be auto-saved
            self._disableButtons();
            self.saveRecord().then(self._enableButtons.bind(self)).guardedCatch(self._enableButtons.bind(self));
        }
        if(canBeSaved && modelName && (confirm || alert)){
                    
                    if(modelName == 'sale.order' && data_changed['product_status']==true){
                        record.data['product_status']=false
                        var def = new Promise(function (resolve, reject) {
                            Dialog.confirm(self, confirm, {
                                confirm_callback: saveAndExecuteAction,
                            }).on("closed", null, reject);
                        });
                    }else{
                        
                        saveAndExecuteAction();
                    }
                
            
        }else{
            saveAndExecuteAction();
        }
        
    },
});




});
