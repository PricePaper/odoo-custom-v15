# See LICENSE file for full copyright and licensing details.

from . import models
# from . import wizard

from odoo import api, SUPERUSER_ID


def pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    warehouse = env.ref("stock.stock_warehouse_comp_rule")
    location = env.ref("stock.stock_location_comp_rule")
    picking = env.ref("stock.stock_location_comp_rule")
    warehouse.domain_force = []
    location.domain_force = []
    picking.domain_force = []
