//--------------------------------------------------------------------------
// Add value of latitude and longitude of google map snippet
//--------------------------------------------------------------------------
odoo.define('theme_clarico_vega.google_map_snippet_backend',function(require) {
'use strict';
    var core = require('web.core');
    var rpc = require('web.rpc');
    var weContext = require('web_editor.context');
    var options = require('web_editor.snippets.options');
    var wUtils = require('website.utils');
    var _t = core._t;
        var set_js_map_generate = options.Class.extend({
            popup_template_id: "google_map_editor_template",
            popup_title: _t("Address information"),
            value_configure: function(type,value) {
                var self = this;
                var def = wUtils.prompt({
                    'id': this.popup_template_id,
                    'window_title': this.popup_title,
                    'input': _t("Your location"),
                    'init': function () {
                        var $group = this.$dialog.find('div.form-group');
                        $group.find('input.form-control').addClass('location_dynamic d-none');
                        $group.find('input.form-control').before('<input class="location_selection_opt" id="static_loc" type="radio" name="radio_group" checked/> Enter Manually <br/> <input class="location_selection_opt" id="dynamic_loc" type="radio" name="radio_group" /> Available Address');
                        $group.find('input.form-control').after('<div class="col-md-8 static_location d-none"><input class="static_location" type="text"/></div>');
                        $group.find('input.static_location').after("<span class='static_address_format_span static_location'><span class='show-format-span'>Either Address or Latitude and Longitude as below.</span><span class='address_span'>- 16a, Little London, Milton Keynes, MK19 6HT</span><span class='lat_long_span'>- 57.815637,-101.137504</span></span>");
                        $group.append("<div class='google_map_size_div'><label class='col-md-4 col-form-label'>Map Width:</label><div class='width_div col-md-8'><input type='text' name='width' class='map_input_ele' value=''/> PX</div><label class='col-md-4 col-form-label'>Map Height:</label><div class='height_div col-md-8'><input type='text' name='height' class='map_input_ele' value=''/> PX</div></div>");
                        /* Get dynamically address of company*/
                        return rpc.query({
                            model: 'website',
                            method: 'get_default_company_address',
                            args: [''],
                            context: weContext.get()
                        });
                     }
                });
                def.then(function (result) {

                    var $dialog = result.dialog;
                    if($($dialog).find('#static_loc').prop("checked")){
                        var val = $($dialog).find('input.static_location').val();
                    }
                    else{
                        var val = result.val;
                    }

                    if (!val) {
                        return;
                    }
                    else{
                        var getValue = val;
                        var lat_long = getValue.split(',');
                        var dialog = self.$($dialog).find('.btn-primary');
                        var width_val = $dialog.find('.width_div input').val();
                        var height_val = $dialog.find('.height_div input').val();
                        if($.isNumeric(lat_long)){
                             self.$target.html('<div class="mapouter" style="width:'+ width_val +'px;height:'+ height_val +'px;"><div class="gmap_canvas"><iframe width="100%" height="100%" id="gmap_canvas" src="https://maps.google.com/maps?q=' + lat_long[0] + ',' + lat_long[1] +'&amp;t=&amp;z=16&amp;ie=UTF8&amp;width=100%&amp;hl=en&amp;iwloc=&amp;output=embed" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" allowfullscreen></iframe></div><style>.gmap_canvas {overflow:hidden;background:none!important;height:100%;width:100%;}</style></div>');
                        }
                        else{
                             self.$target.html('<div class="mapouter" style="width:'+ width_val +'px;height:'+ height_val +'px;"><div class="gmap_canvas"><iframe width="100%" height="100%" id="gmap_canvas" src="https://maps.google.com/maps?q=' + lat_long +'&amp;t=&amp;z=16&amp;ie=UTF8&amp;width=100%&amp;hl=en&amp;iwloc=&amp;output=embed" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" allowfullscreen></iframe></div><style>.gmap_canvas {overflow:hidden;background:none!important;height:100%;width:100%;}</style></div>');
                        }
                        dialog.trigger('click');
                    }
                });
                return def;
            },
             onBuilt: function () {
                var self = this;
                this._super();
                this.value_configure('click').guardedCatch(function () {
                    self.getParent()._onRemoveClick($.Event( "click" ));
                });
             },
        });
        options.registry.js_map_generate = set_js_map_generate.extend({
            cleanForSave: function(){
                this.$target.addClass("hidden");
            }
        });

});

