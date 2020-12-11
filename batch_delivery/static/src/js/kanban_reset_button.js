odoo.define('batch_delivery.kanban_reset_button', function (require) {

    var KanbanController = require('web.KanbanController');
    var KanbanView = require('web.KanbanView');
    var viewRegistry = require('web.view_registry');
    var framework = require('web.framework');


    var KanbanButtonController = KanbanController.extend({

        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            this.$buttons = $('<button/>', {
                class: ['btn btn-primary o_kanban_discard']
                }).text(_('RESET')).on('click', this._onKanbanReset.bind(this)).appendTo($node);
        },

        _onKanbanReset: function () {
            framework.blockUI();
            var self = this;
            this._rpc({
                model: 'stock.picking',
                method: 'reset_picking_with_route'
            }).then(function () {
                self.reload();
            }).always(framework.unblockUI.bind(framework));
        },

        _onDeleteColumn: function (event) {
            var self = this;
            var column = event.target;
            this._rpc({
                model: column.relation,
                method: 'write',
                args: [[column.id], {set_active: false}],
                context: {}
            }).then(function(r){
                self.reload();
            });
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

