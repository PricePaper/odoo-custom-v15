/** @odoo-module **/

import { patch } from 'web.utils';

const Domain = require('web.Domain');
const pyUtils = require('web.py_utils');
const SearchBar = require("web.SearchBar");
const ActionModel = require("web.ActionModel");
const ControlPanelModelExtension = require("web/static/src/js/control_panel/control_panel_model_extension.js");


patch(SearchBar.prototype, 'web_search_with_and', {
    _onWindowKeydown(ev) {

        if (ev.shiftKey) {
            if (ev.key == "Enter" || ev.key == 'Shift') {

                this.model.config.context.webSearchWithOR = true;
            }
            else {

                this.model.config.context.webSearchWithOR = false;
            }
        }
        else {
            this.model.config.context.webSearchWithOR = false;
        }
        this._super(...arguments);
    },
});


patch(ControlPanelModelExtension.prototype, 'web_search_with_and', {
    _getAutoCompletionFilterDomain(filter, filterQueryElements) {
        // return this._super(...arguments);
        // console.log(filter.filterQueryElements)

        const domains = filterQueryElements.map(({
            label,
            value,
            operator
        }) => {
            let domain;
            if (filter.filterDomain) {
                domain = Domain.prototype.stringToArray(
                    filter.filterDomain, {
                    self: label,
                    raw_value: value,
                }
                );
            } else {
                domain = [[filter.fieldName, operator, value]];
            }
            return Domain.prototype.arrayToString(domain);
        });
        
        if (this.config.context.webSearchWithOR) {
            return pyUtils.assembleDomains(domains, 'OR');
        } else {
            return pyUtils.assembleDomains(domains, 'AND');
        }
    }
});


patch(ActionModel.prototype, 'web_search_with_and', {
    _getFacets() {
        let self = this;
        let facets = this._super(...arguments);

        if (!self.config.context.webSearchWithOR) {
            _(facets).each(function (facet) {
                if (facet.type == 'field' && facet.separator == self.env._t("or")) {
                    facet.separator = self.env._t("and")
                }
            })
        }
        return facets;
    }
});
