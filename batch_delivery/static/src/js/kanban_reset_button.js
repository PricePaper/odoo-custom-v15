odoo.define('batch_delivery.kanban_reset_button', function (require) {


var core = require('web.core');
var KanbanController = require('web.KanbanController');
var KanbanView = require('web.KanbanView');
var viewRegistry = require('web.view_registry');
var framework = require('web.framework');

var qweb = core.qweb;


var KanbanButtonController = KanbanController.extend({
	init: function () {
    	this._super.apply(this, arguments);
    },

    renderButtons: function ($node) {
        this.$buttons = $(qweb.render('KanbanReset.buttons'));
        this.$buttons.on('click', '.o_kanban_discard', this._onKanbanReset.bind(this));
        this.$buttons.appendTo($node);

    },

    _onKanbanReset: function () {
        framework.blockUI();
        var self = this;
        this._rpc({
            model: 'stock.picking',
            method: 'reset_picking_with_route',
            args: [this.initialState.res_ids],
        }).then(function () {
            self.reload();
        }).always(framework.unblockUI.bind(framework));
    },
});

var KanbanButtonView = KanbanView.extend({
    config: _.extend({}, KanbanView.prototype.config, {
        Controller: KanbanButtonController,
    }),
});

viewRegistry.add('kanban_reset', KanbanButtonView);

});

