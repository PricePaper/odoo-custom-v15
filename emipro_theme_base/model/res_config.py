# -*- coding: utf-8 -*-
"""
    This model is used to create a boolean social sharing options.
"""
import base64
from odoo import fields, models, tools, api
from odoo.modules.module import get_resource_path


class ResConfig(models.TransientModel):
    _inherit = "res.config.settings"

    is_load_more = fields.Boolean(string='Load More', related='website_id.is_load_more', readonly=False,
                                  help="Load next page products with Ajax")
    load_more_image = fields.Binary(string='Load More Image', related='website_id.load_more_image', readonly=False,
                                    help="Display this image while load more applies.")
    button_or_scroll = fields.Selection(related='website_id.button_or_scroll', required=True, readonly=False,
                                        help="Define how to show the pagination of products in a shop page with on "
                                             "scroll or button.")
    prev_button_label = fields.Char(string='Label for the Prev Button', related='website_id.prev_button_label',
                                    readonly=False, translate=True)
    next_button_label = fields.Char(string='Label for the Next Button', related='website_id.next_button_label',
                                    readonly=False, translate=True)
    is_lazy_load = fields.Boolean(string='Lazyload', related='website_id.is_lazy_load', readonly=False,
                                  help="Lazy load will be enabled.")
    lazy_load_image = fields.Binary(string='Lazyload Image', related='website_id.lazy_load_image', readonly=False,
                                    help="Display this image while lazy load applies.")
    banner_video_url = fields.Many2one('ir.attachment', "Video URL", related='website_id.banner_video_url',
                                       help='URL of a video for banner.', readonly=False)
    number_of_product_line = fields.Selection(related='website_id.number_of_product_line', readonly=False,
                                              string="Number of lines for product name",
                                              help="Number of lines to show in product name for shop.")
    is_auto_play = fields.Boolean(string='Slider Auto Play', related='website_id.is_auto_play',
                                  default=True, readonly=False)
    is_pwa = fields.Boolean(string='PWA', related='website_id.is_pwa', readonly=False, help="Pwa will be enabled.")
    pwa_name = fields.Char(string='Name', related='website_id.pwa_name', readonly=False)
    pwa_short_name = fields.Char(string='Short Name', related='website_id.pwa_short_name', readonly=False)
    pwa_theme_color = fields.Char(string='Theme Color', related='website_id.pwa_theme_color', readonly=False)
    pwa_bg_color = fields.Char(string='Background Color', related='website_id.pwa_bg_color', readonly=False)
    pwa_start_url = fields.Char(string='Start URL', related='website_id.pwa_start_url', readonly=False)
    app_image_512 = fields.Binary(string='Application Image(512x512)', related='website_id.app_image_512',
                                  readonly=False)
    is_price_range_filter = fields.Boolean(string='Price Range Filter', related='website_id.is_price_range_filter',
                                           readonly=False, help="Enable the price range filter")
    price_filter_on = fields.Selection(related='website_id.price_filter_on', readonly=False)
    option_out_of_stock = fields.Boolean(related='website_id.option_out_of_stock', readonly=False)
    text_out_of_stock = fields.Char(related='website_id.text_out_of_stock', readonly=False)
    b2b_hide_details = fields.Boolean(related='website_id.b2b_hide_details', readonly=False)
    text_b2b_hide_details = fields.Char(related='website_id.text_b2b_hide_details', readonly=False)
    b2b_hide_add_to_cart = fields.Boolean(related='website_id.b2b_hide_add_to_cart', readonly=False)
    b2b_hide_price = fields.Boolean(related='website_id.b2b_hide_price', readonly=False)
    allow_reorder = fields.Boolean(string='Allow Reorder', default=False,
                                   related='website_id.allow_reorder', readonly=False,
                                   help='Enable this to allow user reorder the existing sales orders from website')
    is_b2b_message = fields.Boolean(related='website_id.is_b2b_message', readonly=False)
    b2b_checkout = fields.Boolean(related='website_id.b2b_checkout', readonly=False)

    @api.onchange('is_load_more')
    def get_value_icon_load_more(self):
        """
        get lazy load icon
        @return: None
        """
        if not self.is_load_more:
            img_path = get_resource_path('emipro_theme_base', 'static/src/img/Loadmore.gif')
            with tools.file_open(img_path, 'rb') as f:
                self.load_more_image = base64.b64encode(f.read())

    @api.onchange('is_lazy_load')
    def get_value_icon_lazy_load(self):
        """
        check for lazyload
        @return:
        """
        if not self.is_lazy_load:
            img_path = get_resource_path('emipro_theme_base', 'static/src/img/Lazyload.gif')
            with tools.file_open(img_path, 'rb') as f:
                self.lazy_load_image = base64.b64encode(f.read())

    @api.onchange('b2b_hide_details')
    def _onchange_b2b_hide_details(self):
        self.b2b_hide_add_to_cart = False
        self.b2b_hide_price = False
        self.is_b2b_message = False
        if self.b2b_hide_details:
            self.b2b_hide_add_to_cart = True

    @api.model
    def get_values(self):
        """
        get params
        @return: super object
        """
        res = super(ResConfig, self).get_values()
        res.update(
            allow_reorder=self.env['website'].sudo().get_current_website().allow_reorder
        )
        return res
