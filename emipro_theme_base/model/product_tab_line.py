
from odoo import api, fields, models
from odoo.tools.translate import html_translate


class ProductTabLine(models.Model):
    _name = "product.tab.line"
    _inherit = ['website.published.multi.mixin']
    _description = 'Product Tab Line'
    _order = "sequence, id"
    _rec_name = "tab_name"

    def _get_default_icon_content(self):
        return """
            <span class="fa fa-info-circle mr-2"/>
            """

    product_id = fields.Many2one('product.template', string='Product Template')
    tab_name = fields.Char("Tab Name", required=True, translate=True)
    tab_content = fields.Html("Tab Content", sanitize_attributes=False, translate=html_translate, sanitize_form=False)
    icon_content = fields.Html("Icon Content", translate=html_translate, default=_get_default_icon_content)
    website_ids = fields.Many2many('website', help="You can set the description in particular website.")
    sequence = fields.Integer('Sequence', default=1, help="Gives the sequence order when displaying.")
    tab_type = fields.Selection([('specific product', 'Specific Product'), ('global', 'Global')], string='Tab Type')

    def check_tab(self, current_website, tab_website_array):
        """
        check tab for display
        @param current_website: current website
        @param tab_website_array: website array
        @return: Boolean
        """
        if current_website in tab_website_array or len(tab_website_array) == 0:
            return True
        return False

    @api.onchange('tab_type')
    def onchange_tab_type(self):
        """
        onchange for tab type
        """
        if self.tab_type == 'global':
            self.product_id = None
