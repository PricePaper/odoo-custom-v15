/** @odoo-module **/
import contentMenu from 'website.contentMenu';
import weWidgets from 'wysiwyg.widgets';
import {_t} from 'web.core';
import core from 'web.core';
var qweb = core.qweb;

contentMenu.EditMenuDialog.include({
    // Menu edit button click method
    _onEditMenuButtonClick: function (ev) {
        var $menu = $(ev.currentTarget).closest('[data-menu-id]');
        var menuID = $menu.data('menu-id');
        var menu = this.flat[menuID];
        if (menu) {
            var dialog = new weWidgetsMenuEntryDialog(this, {dialogClass: 'dialog_dynamic_menu',}, null, _.extend({
                menuType: menu.fields['is_mega_menu'] ? 'mega' : undefined,
                class: 'custom_class',
            }, menu.fields));
            dialog.on('save', this, link => {
                _.extend(menu.fields, {
                    'name': _.unescape(link.content),
                    'url': link.url,
                    'new_window': link.isNewWindow,
                    'is_dynamic_menu': link.is_dynamic_menu,
                    'menu_label_text': link.menu_label_text,
                    'menu_label_text_color': link.menu_label_text_color,
                    'is_highlight_menu': link.is_highlight_menu,
                });
                $menu.find('.js_menu_label').first().text(menu.fields['name']);
                var data = $menu.find('.te_highlight_menu');
                if (menu.fields['is_highlight_menu']){
                    if ($menu.find('.te_highlight_menu').length == 0){
                        $menu.find('.form-control').first().append('<span class="badge te_highlight_menu ml-2" style="cursor: pointer;"><span class="fa fa-paint-brush"/></span>');
                    }
                }
                else{
                   $menu.find('.te_highlight_menu').first().remove();
                }
            });
            dialog.open();
        } else {
            Dialog.alert(null, "Could not find menu entry");
        }
    },
    // Add new menu button click method
    _onAddMenuButtonClick: function (ev) {
        var menuType = ev.currentTarget.dataset.type;
        var dialog = new weWidgetsMenuEntryDialog(this, {dialogClass: 'dialog_dynamic_menu'}, null, {
            menuType: menuType,
        });
        dialog.on('save', this, link => {
            var newMenu = {
                'fields': {
                    'id': _.uniqueId('new-'),
                    'name': _.unescape(link.content),
                    'url': link.url,
                    'new_window': link.isNewWindow,
                    'is_mega_menu': menuType === 'mega',
                    'sequence': 0,
                    'parent_id': false,
                    'is_dynamic_menu': link.is_dynamic_menu,
                    'menu_label_text': link.menu_label_text,
                    'menu_label_text_color': link.menu_label_text_color,
                    'is_highlight_menu': link.is_highlight_menu,
                },
                'children': [],
                'is_homepage': false,
            };
            this.flat[newMenu.fields['id']] = newMenu;
            this.$('.oe_menu_editor').append(
                qweb.render('website.contentMenu.dialog.submenu', {submenu: newMenu})
            );
        });
        dialog.open();
    },
});
var weWidgetsMenuEntryDialog = contentMenu.MenuEntryDialog.extend({
});
