odoo.define('batch_delivery.kanban_reset_button', function (require) {


    var KanbanController = require('web.KanbanController');
    var KanbanView = require('web.KanbanView');
    var viewRegistry = require('web.view_registry');
    var framework = require('web.framework');
    const {_t} = require('web.core');


    var KanbanButtonController = KanbanController.extend({

       renderButtons: function ($node) {
       this._super.apply(this, arguments);
        this.$buttons = $('<button/>', {
            class: ['btn btn-primary o_kanban_discard']
        }).text(_t('RESET'))
        this.$buttons.on('click', this._onKanbanReset.bind(this));
        ;

        this.controlPanelProps.cp_content = {
            $buttons: this.$buttons,
        };

         },

        _reloadPage: function () {
            window.location.reload();
        },

        _onKanbanReset: function () {

            framework.blockUI();
            var self = this;
            self.displayNotification({ title: _t('Resetting'), message: _t('Please Wait..!'), sticky: true, type: 'info' });
            this._rpc({
                model: 'stock.picking',
                method: 'reset_picking_with_route'
            });
            this._reloadPage();
        },

        _onDeleteColumn: function (event) {
            var self = this;
            var column = event.target;
            if (!column.isEmpty()) {
                 self.displayNotification({ title: _t('Alert!!'), message: _t('Please remove pickings from route before delete.'), sticky: true, type: 'danger' });
                 return;
            }
            this._rpc({
                model: column.relation,
                method: 'write',
                args: [[column.id], {set_active: false}],
                context: {}
            });
            this._reloadPage();
    },

    });

    var KanbanButtonView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Controller: KanbanButtonController,
        }),
    });

    viewRegistry.add('kanban_reset', KanbanButtonView);

    return {
        KanbanButtonController: KanbanButtonController,
        KanbanButtonView: KanbanButtonView,       
    };

});

