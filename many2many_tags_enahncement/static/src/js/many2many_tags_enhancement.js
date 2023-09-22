odoo.define('many2many_tags_enahncement.many2many_tags', function (require) {
"use strict";

var relational_fields = require('web.relational_fields');

var FieldMany2ManyTags = relational_fields.FieldMany2ManyTags;
var core = require('web.core');

var _t = core._t;
var _lt = core._lt;
var qweb = core.qweb;



FieldMany2ManyTags.include({
    _getRenderTagsContext: function () {
        var elements = this.value ? _.pluck(this.value.data, 'data') : [];
        if (this.value.data.length==0 && this.value.res_ids.length >0){
            this.value.data=this.value.custom_data
            return {
            colorField: this.colorField,
            elements: this.value.custom_data,
            hasDropdown: true,
            readonly: this.mode === "readonly",
        };
        }
        else{
        
        return {
            colorField: this.colorField,
            elements: elements,
            hasDropdown: this.hasDropdown,
            readonly: this.mode === "readonly",
        };
    }
    },
     /**
     * @private
     * @param {any} id
     */
    _removeTag: function (id) {
        var record = _.findWhere(this.value.data, {res_id: id});
        if(record== undefined){
            this._setValue({
            operation: 'FORGET',
            ids: [id],
        });
        }
        else{
            this._setValue({
            operation: 'FORGET',
            ids: [record.id],
        });
        }
        
    },
    _renderTags:async function () {
        var self=this
        if (this.value.data.length==0 && this.value.res_ids.length >0){
        await this._rpc({
                model: this.value.model,
                method: 'search_read',
                domain: [['id', 'in', this.value.res_ids]],
                fields: ['id','display_name'],
            }).then(function (data) {
                self.value.custom_data=data

                self.$el.html(qweb.render(self.tag_template, self._getRenderTagsContext()));
            });
        }
        else{
            this.$el.html(qweb.render(this.tag_template, this._getRenderTagsContext()));

        }
        
    }
});
});
