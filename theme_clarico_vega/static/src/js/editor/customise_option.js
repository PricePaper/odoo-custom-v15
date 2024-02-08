//--------------------------------------------------------------------------
//Customise Option file included
//--------------------------------------------------------------------------
odoo.define('theme_clarico_vega.options', function (require) {
'use strict';

var core = require('web.core');
var QWeb = core.qweb;

QWeb.add_template('/theme_clarico_vega/static/src/xml/customise_option.xml');
})
