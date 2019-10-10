from odoo import models, fields, api,_

class WebsiteScrapingConfig(models.Model):
    _name = "website.scraping.cofig"
    _description = "Website Scraping Config"

    name = fields.Char(string='Name')
    home_page_url = fields.Char('Home page URL')
    username = fields.Char(string='Username')
    password = fields.Char(string='Password')
    competitor = fields.Selection([('rdepot', 'Restaurant Depot'), ('wdepot', 'Webstaurant Store')], string='Competitor')


WebsiteScrapingConfig
