odoo.define("pp_address_book.address_book", function (require) {
    "use strict";

    var core = require("web.core");
    var ajax = require('web.ajax');
    var _t = core._t;
    var sAnimation = require('website.content.snippets.animation');
    $.blockUI.defaults.css.border = '0';
    $.blockUI.defaults.css["background-color"] = '';
    $.blockUI.defaults.overlayCSS["opacity"] = '0.9';

    sAnimation.registry.userAddressesSettings = sAnimation.Class.extend({
        selector: ".address_edit_book",

        events: {
            "change #country_id": "_changeCountry",
            "click .discard": "_discard"
        },

        _changeCountry: function (ev) {
            var country_id = ev.currentTarget.value;
            var $state = this.$target.find("[name='state_id']");
            var $first = $state.find('option').first();
            $state.find('option').remove().end().append($first);
            if (country_id) {
                var url = `/shop/country_infos/${country_id}`;
                ajax.jsonRpc(url, 'call', { "mode": "" }).then(function (response) {
                    if (response) {
                        var state = response.states;
                        var $option = ""
                        state.forEach(function (item) {
                            $option += `<option value=${item[0]}>${item[1]}</option>`;
                        })
                        if ($option.length > 0) {
                            $state.parents(".state_form").show();
                            $state.find('option').end().append($option);
                        } else {
                            $state.parents(".state_form").hide();
                        }
                    }
                })
            }
        },

        _discard: function (ev) {
            window.location.href = "/my/address/book";
        }
    });

    sAnimation.registry.portal_access = sAnimation.Class.extend({
        selector: ".address_card",

        events: {
            "click .portal_access": "portalAcess",
            "click .portal_access_deny":"portalRevoke"
        },


        portalRevoke:function(ev){
            var msg = _t("We are Revoking Access, please wait ...");
            $.blockUI({
                'message': '<h2 class="text-white"><img src="/web/static/img/spin.png" class="fa-pulse"/>' +
                    '    <br />' + msg +
                    '</h2>'
            });
            var partner_id = $(ev.currentTarget).attr('data-partner_id')
            var url = `/portal/grant/access`;
            ajax.jsonRpc(url, 'call', { "partner_id": partner_id ,"portal":false}).then(function (response) {
                if (response.error) {
                    $.unblockUI()
                    alert("There's an error while revoking the access , Kindly Contact us for furtther steps")

                }
                else{
                    location.reload()
                }
            });

        },
        portalAcess: function (ev) {
            var msg = _t("We are Granting Access, please wait ...");
            $.blockUI({
                'message': '<h2 class="text-white"><img src="/web/static/img/spin.png" class="fa-pulse"/>' +
                    '    <br />' + msg +
                    '</h2>'
            });
            var partner_id = $(ev.currentTarget).attr('data-partner_id')
            var url = `/portal/grant/access`;
            ajax.jsonRpc(url, 'call', { "partner_id": partner_id }).then(function (response) {
                if (response.error) {
                    $.unblockUI()
                    alert("This email address is already been used by another user , Kindly Contact us for furtther steps")
                }
                else{
                    location.reload()
                }
            });

        }
    });



})