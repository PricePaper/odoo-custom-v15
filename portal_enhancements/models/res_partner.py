# -*- coding: utf-8 -*-

from odoo import fields, models, api, _,SUPERUSER_ID
from odoo.exceptions import UserError, Warning

class ResPartnerBank(models.Model):
    _inherit='res.partner.bank'

    signature = fields.Binary(string='Signature')
    # acc_type = fields.Selection([('saving','Savings'),('checking','Checking')])

class ResPartner(models.Model):
    _inherit = 'res.partner'

    portal_access_level = fields.Selection([('manager', 'Manager'), ('user', 'Administrator')],
                                        string='Portal Access Level')
    portal_company_ids = fields.Many2many('res.partner', 'portal_company_partner_rel','res_partner_id', 'portal_partner_id',
                                          string="Accessible Companies", domain=[('is_company','=',True)], tracking=True)
    portal_partner_ids = fields.Many2many('res.partner', 'portal_company_partner_rel', 'portal_partner_id', 'res_partner_id',
                                          string="Portal Users", domain=[('is_company', '=', False)])
    has_portal_access = fields.Boolean(string="Portal Access", compute="_compute_portal_access")

    portal_contact_ids = fields.One2many('portal.contacts', 'portal_partner_id', string="Accessible Contacts")

    portal_model_access = fields.One2many('portal.model.access', 'portal_partner_id',
                                          string="Manage Model Access Rights")
    portal_admin_id = fields.Many2one('res.partner', string="Related Administrator", domain=[('portal_access_level','=','user')])
    portal_manager_ids = fields.One2many('res.partner', 'portal_admin_id', string="Managers", domain=[('portal_access_level','=','manager')])
    # dba = fields.Char(string='Doing Business As')
    year_established = fields.Integer(string='Year Established')
    established_state = fields.Many2one("res.country.state", string='Established State')
    resale_taxexempt = fields.Selection([('resale','Resale'),('tax_exempt','Tax Exempt'),('none','None')],string='Resale or Tax Exempt')
    typeofbusiness = fields.Selection([('corporation', 'Corporation'),('partnership', 'Partnership'),('sole_proprietor', 'Sole Proprietor'),('llc', 'LLC')],string='Type of Business')
    is_verified = fields.Boolean(string='Verified',default=False)
    basic_verification_submit = fields.Boolean(string='Basic Verification',default=False)
    businesss_registration_information = fields.Boolean(string='Basic Resgistration',default=False)
    business_verification_status = fields.Selection([('submit','Submitted'),('approved','approved'),('reject','Rejected')])
    rejection_reason = fields.Char('Rejection Reason')
    tax_exempt_certifcate_id = fields.Many2one('documents.document',string='Tax Exempt Certificate Id')
    payment_value = fields.Selection([
        ('ach_debit','Ach Debit'),
        ('paid_delivery','Pay On Delivery'),
        ('apply_credit','Apply Credit'),
        ('credit_card','Credit Card'),
        ],default='credit_card')

    can_create_orders = fields.Boolean('Can create orders from website?',default=False)

    portal_parent_ids = fields.Many2many('res.users', 'portal_user_partner_rel',
                                             'portal_child_partner_id', 'portal_parent_user_id',
                                             string="Portal Parent User")
    sign_request_business = fields.Many2one('sign.request')

    partner_credit = fields.Many2one('partner.credit')

    def create_helpdesk_ticket_approval(self):
        team_id = self.env['ir.config_parameter'].sudo().get_param('portal_enhancements.helpdesk_team_onbaording')
        
        helpdesk_vals = {
                'name':f'New Customer: "{self.name}" Approval',
                'partner_id':self.id
            }
        if team_id:
                helpdesk_vals['team_id'] = int(team_id)
        ticket_id = self.env['helpdesk.ticket'].with_user(SUPERUSER_ID).create(helpdesk_vals)
        acttion = self.env.ref('price_paper.res_partner_pricepaper_vat_edit_permission_action')
        ticket_id.message_post(body=("New Customer have completed the onboarding process kindly check and take appropriate actions") + " <a href='/web#id=%s&action=%s&model=res.partner&view_type=form' data-oe-model=res.partner>%s</a>" % (self.id,acttion.id,self.name))

        return True

    def verify_signatures(self):
        partner = self
        print('partner.resale_taxexempt')
        # 'context':{
            #     'default_portal_user':partner.id,
            #     'default_contact_name':contact_name,
            #     'default_contact_email':self.email_from
            # }
            # 'res_id': self.id,
        payment_value = 'Paid at time of delivery (cash or check)'
        if partner.payment_value =='ach_debit':
            payment_value  ='Automatic ACH debit after delivery'
        if partner.payment_value=='credit_card':
            payment_value = 'Credit card (3% upcharge)'
        if partner.payment_value=='apply_credit':
            payment_value='Applied For credit'

        business_type = 'Reseller with a valid resale certificate'
        if partner.resale_taxexempt =='tax_exempt':
            business_type = 'Tax exempt with a valid tax exempt certificate'
        elif partner.resale_taxexempt =='None':
            business_type ='Sales tax on all purchases'
        else:
            business_type = 'Reseller with a valid resale certificate'
        return {
            'name': 'Portal Approval',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'portal.approval',
            'target':'new',
            'context':{
                'default_business_registration_type':business_type,
                'default_business_resale_sign_document':self.sign_request_business.id,
                'default_payment_type':payment_value
                # 'default_contact_name':contact_name,
                # 'default_contact_email':self.email_from
            }
            
        }

    def write(self, vals):
        current_company_ids = self.portal_company_ids

        res = super(ResPartner, self).write(vals)

        if 'portal_company_ids' in vals:
            removed_companies = current_company_ids - self.portal_company_ids
            added_companies = self.portal_company_ids - current_company_ids
            if removed_companies:
                remove_contacts = self.portal_contact_ids.filtered(lambda x: x.partner_id.id in removed_companies.ids or x.parent_id.id in removed_companies.ids)
                remove_contacts.unlink()

                removed_company_names = '<li>' + '</li><li>'.join(removed_companies.mapped('name')) + '</li>'
                self.message_post(body=f"Companies Removed:<br/><ul><span style='color: red;'>{removed_company_names}</span></ul>")

            if removed_companies and self.child_ids:
                for child in self.child_ids:
                    child.portal_company_ids = child.portal_company_ids - removed_companies

            if added_companies:
                self.portal_contact_ids = [(0, 0, {'partner_id': company.id}) for company in added_companies]
                added_company_names = '<li>' + '</li><li>'.join(added_companies.mapped('name')) + '</li>'
                self.message_post(
                    body=f'Companies Added:<br/><ul><span style="color: green;">{added_company_names}</span></ul>')

        for key in ('portal_company_ids', 'portal_partner_ids', 'portal_contact_ids'):
            if key in vals:
                self.clear_caches()
                break

        return res

    def _compute_portal_access(self):
        for partner in self:
            if partner.user_ids:
                user_id = partner.user_ids[0]
                partner.has_portal_access = user_id and all(user_id.has_group(group) for group in ('base.group_portal', 'portal_enhancements.group_portal_enhanced_record_access'))
            else:
                partner.has_portal_access = False

    def action_add_contacts(self):

        origin_id = self._context.get('origin_id', None)
        if self._context.get('origin_model', None) == 'res.partner' and origin_id:

            contact_ids = self.env['res.partner'].browse([origin_id]).portal_contact_ids.filtered(lambda x: x.parent_id.id == self.id).partner_id

            wizard_id = self.env['add.portal.contacts'].create({'company_id': self.id,
                                                             'portal_wizard_contact_ids': [(6, 0, contact_ids.ids)]})

            return {
                'name': _("Add Contacts"),
                'view_mode': 'form',
                'res_model': 'add.portal.contacts',
                'res_id': wizard_id.id,
                'type': 'ir.actions.act_window',
                'domain': [()],
                'target': 'new',
            }
        return False

    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        if self.portal_access_level and self.parent_id:
            company_list = []
            for company in self.portal_company_ids:
                if company._origin not in self.parent_id.portal_company_ids:
                    company_list.append(company.display_name)
            if company_list:
                raise UserError(_(f"To designate the selected user as a Portal Administrator, please ensure that they have "
                              f"access to the following companies first.\n"+'\n'.join(company for company in company_list)))

    @api.onchange('portal_access_level')
    def _onchange_portal_access_level(self):
        if self.portal_access_level == 'user' and self.parent_id:
            self.parent_id = False
            return {
                'warning': {
                    'title': 'Warning!',
                    'message': 'Changing the "Portal Access Level" from "Manager" to "Administrator" will remove the currently assigned Administrator.'
                }
            }

    def action_add_companies(self):

        wizard_id = self.env['add.portal.companies'].create({'parent_id': self.parent_id.id, 'portal_user_id': self.id,
                                                             'portal_wizard_company_ids': [(6, 0, self.portal_company_ids.ids)]})
        ctx = dict(self._context)
        ctx.update({'related_companies': self.parent_id.portal_company_ids.ids})
        return {
            'name': _("Add Companies"),
            'view_mode': 'form',
            'res_model': 'add.portal.companies',
            'res_id': wizard_id.id,
            'type': 'ir.actions.act_window',
            'domain': [()],
            'context': ctx,
            'target': 'new',
        }

    @api.model
    def default_get(self, fields):

        model_xml_ids = ["sale.model_sale_order", "account.model_account_move", "purchase.model_purchase_order", "crm.model_crm_lead",
                         "project.model_project_project", "helpdesk.model_helpdesk_ticket", "calendar.model_calendar_event"]
        res = super(ResPartner, self).default_get(fields)
        if 'portal_model_access' in fields:
            res['portal_model_access'] = [(0, 0, {'model_id': self.env.ref(model).id, 'is_model_accessible': False}) for model in model_xml_ids]
        return res

    def _check_portal_model_access(self, model: str):
        access_record = self.portal_model_access.filtered(lambda x: x.model_id.model == model)
        if access_record and access_record.is_model_accessible:
            return True
        return False

    def name_get(self):
        res = super(ResPartner, self).name_get()
        result = []
        for partner in res:
            partner_id = self.env['res.partner'].browse(partner[0])
            if partner_id.portal_access_level:
                result.append((partner[0], partner_id.name + ' - Portal User\n'))
            else:
                result.append((partner[0], partner[1]))

        return result

    def action_grant_portal_access(self):
        """
        Handles api call from mobile app.
        Grants portal access to the partner
        @return: result
        """
        self.ensure_one()
        result = []
        result_dict = {'success': True, 'error': False}
        wizard = self.env['portal.wizard'].create({})

        portal_wizard_id = self.env['portal.wizard.user'].create({
                                                                'wizard_id': wizard.id,
                                                                'partner_id': self.id,
                                                                'email': self.email})
        try:
            portal_wizard_id.action_grant_access()
        except Exception as e:
            result_dict['success'] = False
            result_dict['error'] = str(e)

        result.append(result_dict)

        return result
