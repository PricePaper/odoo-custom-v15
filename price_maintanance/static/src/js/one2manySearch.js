odoo.define('price_maintanance.search_field_many_2_many', function (require) {
    "use strict";

    var FieldMany2Many = require('web.relational_fields').FieldMany2Many;
    var FieldOne2Many = require('web.relational_fields').FieldOne2Many;
    FieldOne2Many.include({
     events: _.extend({
            'keyup .oe_search_input': '_onKeyUp'
        }, FieldOne2Many.prototype.events),

        _render: function () {
            var self = this;
            if(this.attrs.options.custom_search){
                $(".search_block").remove()
                return this._super.apply(this, arguments).then(function () {
                    if(self.view.arch.tag == 'kanban' && self.$el.hasClass('o_field_x2many_kanban')){
                        var search = "<div style='display:flex;align-items:center;justify-content:space-between;' class='search_block'>" +
                                            "<div class='fa fa-search'/>" +
                                           "<input type='text' class='oe_search_input mb-3 mt-2 ml-2 pl-2' style='width:100%;border-radius:10px;height:30px;border:2px solid #a79d9d;' placeholder='Search...'>" +
                                      "</div>";
                        self.$el.prepend($(search));
                    }
                });
            }
            return this._super()
        },

        _onKeyUp: function (event) {
            var value = $(event.currentTarget).val().toLowerCase();

            document.querySelectorAll('.o_kanban_record').forEach((elm)=>{
                $(elm).toggle($(elm).text().toLowerCase().indexOf(value) > -1)

            });
        },
    })
    FieldMany2Many.include({
        events: _.extend({
            'keyup .oe_search_input': '_onKeyUp'
        }, FieldMany2Many.prototype.events),

        _render: function () {
            var self = this;
            if(this.attrs.options.custom_search){
                $(".search_block").remove()
                return this._super.apply(this, arguments).then(function () {
                    if(self.view.arch.tag == 'kanban' && self.$el.hasClass('o_field_x2many_kanban')){
                        var search = "<div style='display:flex;align-items:center;justify-content:space-between;' class='search_block'>" +
                                            "<div class='fa fa-search'/>" +
                                           "<input type='text' class='oe_search_input mb-3 mt-2 ml-2 pl-2' style='width:100%;border-radius:10px;height:30px;border:2px solid #a79d9d;' placeholder='Search...'>" +
                                      "</div>";
                        self.$el.prepend($(search));
                    }
                });
            }
            return this._super()
        },

        _onKeyUp: function (event) {
            var value = $(event.currentTarget).val().toLowerCase();

            document.querySelectorAll('.o_kanban_record').forEach((elm)=>{
                $(elm).toggle($(elm).text().toLowerCase().indexOf(value) > -1)

            });
        },
    });
});
