/** @odoo-module */

import { OdooEditor } from '@web_editor/../lib/odoo-editor/src/OdooEditor';
const KEYBOARD_TYPES = { VIRTUAL: 'VIRTUAL', PHYSICAL: 'PHYSICAL', UNKNOWN: 'UKNOWN' };
const IS_KEYBOARD_EVENT_UNDO = ev => ev.key === 'z' && (ev.ctrlKey || ev.metaKey);
const IS_KEYBOARD_EVENT_REDO = ev => ev.key === 'y' && (ev.ctrlKey || ev.metaKey);
const IS_KEYBOARD_EVENT_BOLD = ev => ev.key === 'b' && (ev.ctrlKey || ev.metaKey);
import { closestElement } from '@web_editor/static/lib/odoo-editor/src/utils/utils.js';
OdooEditor.prototype._onKeyDown = function _onKeyDown(ev) {
    /*** @override */
    if(!$('#product_configure_model').hasClass('show')) {
        this.keyboardType = ev.key === 'Unidentified' ? KEYBOARD_TYPES.VIRTUAL : KEYBOARD_TYPES.PHYSICAL;
        if (/^.$/u.test(ev.key) && !ev.ctrlKey && !ev.metaKey) {
            const selection = this.document.getSelection();
            if (selection && !selection.isCollapsed) {
                this.deleteRange(selection);
            }
        }
        if (ev.key === 'Backspace' && !ev.ctrlKey && !ev.metaKey) {
            const selection = this.document.getSelection();
            if (selection.isCollapsed) {
                ev.preventDefault();
                this._applyCommand('oDeleteBackward');
            }
        } else if (ev.key === 'Tab') {
            const sel = this.document.getSelection();
            const closestTag = (closestElement(sel.anchorNode, 'li, table', true) || {}).tagName;
            if (closestTag === 'LI') {
                this._applyCommand('indentList', ev.shiftKey ? 'outdent' : 'indent');
            } else if (closestTag === 'TABLE') {
                this._onTabulationInTable(ev);
            } else if (!ev.shiftKey) {
                this.execCommand('insertText', '\u00A0 \u00A0\u00A0');
            }
            ev.preventDefault();
            ev.stopPropagation();
        } else if (IS_KEYBOARD_EVENT_UNDO(ev)) {
            ev.preventDefault();
            ev.stopPropagation();
            this.historyUndo();
        } else if (IS_KEYBOARD_EVENT_REDO(ev)) {
            ev.preventDefault();
            ev.stopPropagation();
            this.historyRedo();
        } else if (IS_KEYBOARD_EVENT_BOLD(ev)) {
            ev.preventDefault();
            ev.stopPropagation();
            this.execCommand('bold');
        }
    }
}
return OdooEditor;
