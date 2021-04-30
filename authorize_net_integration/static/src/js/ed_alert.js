odoo.define('authorize_net_integration.alert', function (require) {
"use strict";
var prompt = function ShowDialogBox(title, content, btn1text, btn2text, functionText, parameterList) {
                var btn1css;
                var btn2css;
                if (btn1text == '') {
                    btn1css = "hidecss";
                } else {
                    btn1css = "showcss";
                }

                if (btn2text == '') {
                    btn2css = "hidecss";
                } else {
                    btn2css = "showcss";
                }
                $("#lblMessage").html(content);                
                $("#ed-dialog").dialog({
                    resizable: false,
                    title: title,
                    modal: true,
                    width: '400px',
                    height: 'auto',
                    bgiframe: false,
                    hide: { effect: 'scale', duration: 400 },

                    buttons: [
                                    {
                                        text: btn1text,
                                        "class": btn1css,
                                        click: function () {

                                            $("#ed-dialog").dialog('close');

                                        }
                                    },
                                    {
                                        text: btn2text,
                                        "class": btn2css,
                                        click: function () {
                                            $("#ed-dialog").dialog('close');
                                        }
                                    }
                                ]
                });
            }

var data = {
    ed_alert: prompt,
};
return data;

});
