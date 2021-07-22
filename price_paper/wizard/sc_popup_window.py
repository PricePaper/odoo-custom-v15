from odoo import fields, models


class StorageContractPopUpWindow(models.TransientModel):
    _name = 'sc.popup.window'
    _description = 'Storage Contract PopUp Window for adding Existing contract'

    partner_id = fields.Many2one('res.partner', string='Customer')
    contract_line_id = fields.Many2one('sale.order.line', string='Storage Contract')

    def add_sc_line(self):
        sc_line = self.contract_line_id
        qty = sc_line.storage_remaining_qty if sc_line.storage_remaining_qty < sc_line.selling_min_qty else sc_line.selling_min_qty
        line = self.env['sale.order.line'].create({
            'product_id': sc_line.product_id.id,
            'storage_contract_line_id': sc_line.id,
            'product_uom_qty': qty,
            'order_id': self._context.get('active_id')
        })
        line.product_id_change()
        line.product_uom_change()


StorageContractPopUpWindow()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
