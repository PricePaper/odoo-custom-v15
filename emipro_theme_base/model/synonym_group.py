# -*- coding: utf-8 -*-
"""
    This model is used to manage group of synonyms
"""
from itertools import chain
from odoo import fields, models, api
from odoo.exceptions import UserError


class SynonymGroup(models.Model):
    """
    Class for Synonyms
    """
    _name = "synonym.group"
    _description = "Synonym Group"
    _order = "id desc"

    name = fields.Char(string='Synonyms Group', required=True,
                       help='Synonyms Group with comma separated keywords(Eg., Mobile,Smartphone,Cellphone)')
    website_id = fields.Many2one(string="Website", comodel_name="website",
                                 help="This group will only accessible for specified website. "
                                      "Accessible for all websites if not specified!")

    @api.model
    def create(self, vals):
        if vals.get('name', False):
            self.check_synonyms_validation(vals.get('name'))
        return super(SynonymGroup, self).create(vals)

    def write(self, vals):
        if vals.get('name', False):
            self.check_synonyms_validation(vals.get('name'))
        return super(SynonymGroup, self).write(vals)

    def check_synonyms_validation(self, synonyms=''):
        """ raise an error in two case:
         1) entered synonym(s) found in other synonym groups, or
         2) a synonym entered multiple times in a single synonym group"""
        synonym_list = [v.strip() for v in synonyms.split(',')]
        if len(set(synonym_list)) != len(synonym_list):
            exist = {synm for synm in synonym_list if synonym_list.count(synm) > 1}
            raise UserError("You have entered '%s' multiple times.\n "
                            "\nMake sure that each synonym is entered only once!" % ', '.join(exist))
        groups = self.search_read([], fields=['name'])
        for synm in synonym_list:
            grps = chain.from_iterable([g.get('name').split(',') for g in groups])
            if synm in grps:
                raise UserError("%s, Synonym is exist in another group." % (synm.capitalize()))
