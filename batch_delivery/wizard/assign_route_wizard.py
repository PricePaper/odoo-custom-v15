# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AssignRouteWizard(models.TransientModel):
    _name = 'assign.route.wizard'
    _description = 'Assign Route'

    line_ids = fields.One2many('assign.route.wizard.line', 'parent_id', string='Assign Route Lines')

    def assign_routes(self):

        pickings = self.env['stock.picking'].search(
            [('state', 'in', ['confirmed', 'assigned', 'in_transit']), ('picking_type_code', '=', 'outgoing'),
             ('route_id', '=', False)])

        # group all potential pickings into a dictionary based on partner_id.
        # this dictionary is later used to assign routes for pickings
        picking_dict = {}
        for picking in pickings:
            if picking.carrier_id and picking.carrier_id.show_in_route:
                if picking.partner_id.id in picking_dict.keys():
                    picking_dict[picking.partner_id.id].append(picking)
                else:
                    picking_dict.update({picking.partner_id.id: [picking]})

        # the below loop assigns routes to the available pickings ready for delivery when route is assigned,
        # batch is auto assigned based in the logic written in stock.picking model
        partners_assigned = []
        for line in self.line_ids:
            if line.route_id:
                line.route_id.set_active = True
            for partner_id in picking_dict.keys():
                if partner_id in partners_assigned:
                    continue
                if line.prior_batch_id.picking_ids.filtered(lambda pic: pic.partner_id.id == partner_id):
                    [picking.write({'route_id': line.route_id.id}) for picking in picking_dict[partner_id]]
                    partners_assigned.append(partner_id)

        # it will preserve the context and domain value for view transition.
        return self.env.ref('batch_delivery.stock_picking_act_route_assign').read()[0]


class AssignRouteWizardLines(models.TransientModel):
    _name = 'assign.route.wizard.line'
    _description = 'Assign Route Line'

    parent_id = fields.Many2one('assign.route.wizard', string='Parent')
    route_id = fields.Many2one('truck.route', string='Route')
    prior_batch_id = fields.Many2one('stock.picking.batch', string='Prior Batch')

    @api.onchange('route_id')
    def onchange_route_id(self):
        return {'domain': {'prior_batch_id': ([('route_id', '=', self.route_id.id)])}}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
