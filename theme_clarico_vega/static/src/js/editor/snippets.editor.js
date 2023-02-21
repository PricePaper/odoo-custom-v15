odoo.define('theme_clarico_vega.snippet.editor', function (require) {
'use strict';

const {qweb, _t, _lt} = require('web.core');
const Dialog = require('web.Dialog');
const weSnippetEditor = require('web_editor.snippet.editor');
var options = require('web_editor.snippets.options');

weSnippetEditor.SnippetsMenu.include({
    events: _.extend({}, weSnippetEditor.SnippetsMenu.prototype.events, {
        'click .o_we_customize_theme_btn_ept': '_onThemeTabClickEpt',
    }),
    tabs: _.extend({}, weSnippetEditor.SnippetsMenu.prototype.tabs, {
        THEME_EPT: 'theme-ept',
    }),
    OptionsTabStructureEpt: [
        ['theme-options-ept', _lt("Theme Settings")],
    ],
    _updateRightPanelContent: function ({content, tab}) {
        this._super(...arguments);
        this.$('.o_we_customize_theme_btn_ept').toggleClass('active', tab === this.tabs.THEME_EPT);
    },
    async _onThemeTabClickEpt(ev) {
        // Note: nothing async here but start the loading effect asap
        let releaseLoader;
        try {
            const promise = new Promise(resolve => releaseLoader = resolve);
            this._execWithLoadingEffect(() => promise, false, 400);
            // loader is added to the DOM synchronously
            await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
            // ensure loader is rendered: first call asks for the (already done) DOM update,
            // second call happens only after rendering the first "updates"

            if (!this.topFakeOptionElEpt) {
                let el;
                for (const [elementName, title] of this.OptionsTabStructureEpt) {
                    const newEl = document.createElement(elementName);
                    newEl.dataset.name = title;
                    if (el) {
                        el.appendChild(newEl);
                    } else {
                        this.topFakeOptionElEpt = newEl;
                    }
                    el = newEl;
                }
                this.bottomFakeOptionElEpt = el;
                this.el.appendChild(this.topFakeOptionElEpt);
            }

            // Need all of this in that order so that:
            // - the element is visible and can be enabled and the onFocus method is
            //   called each time.
            // - the element is hidden afterwards so it does not take space in the
            //   DOM, same as the overlay which may make a scrollbar appear.
            this.topFakeOptionElEpt.classList.remove('d-none');
            const editorPromise = this._activateSnippet($(this.bottomFakeOptionElEpt));
            releaseLoader(); // because _activateSnippet uses the same mutex as the loader
            releaseLoader = undefined;
            const editor = await editorPromise;
            this.topFakeOptionElEpt.classList.add('d-none');
            editor.toggleOverlay(false);

            this._updateRightPanelContent({
                tab: this.tabs.THEME_EPT,
            });
        } catch (e) {
            // Normally the loading effect is removed in case of error during the action but here
            // the actual activity is happening outside of the action, the effect must therefore
            // be cleared in case of error as well
            if (releaseLoader) {
                releaseLoader();
            }
            throw e;
        }
    },
});
options.registry.ThemeOptionsEpt = options.Class.extend({
    pageOptionName: 'ThemeOptionsEpt',
});
});
