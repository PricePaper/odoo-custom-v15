from odoo import api,fields,models,_

class PartnerCredit(models.Model):
    _name='partner.credit'
    _description = "Model for managaing Partner Credit Application"

    partner_id = fields.Many2one('res.partner',string='Customer')
    company = fields.Char(string='Company')
    phone = fields.Char(string='Phone')
    mobile = fields.Char(string='Phone')
    address = fields.Char(string='Address')
    email = fields.Char(string='Email')
    city = fields.Char(string='City')
    zip = fields.Char(string='Zip')
    state = fields.Char('state')
    state_id = fields.Many2one('res.country.state')
    fax = fields.Char(string='Fax')
    corporate_partner_ids = fields.One2many('corporate.partner','partner_credit_id',string='Corporate Partners')
    typeofbusiness = fields.Selection([('corporation', 'Corporation'),('partnership', 'Partnership'),('sole_proprietor', 'Sole Proprietor'),('llc', 'LLC')],string='Type of Business')
    location = fields.Selection([('own','Owned'),('leased','Leased'),('monthly','Monthly Rental'),('other','Other')])
    other_location = fields.Char(string='Location')
    annual_sales_volume = fields.Char(string='Annual Sales Volume')
    account_payable_contact = fields.Char('Account Payable Contact')
    year_established = fields.Integer(string='Year Established')
    no_emp = fields.Char(string='Num of Employess')
    time_present_location = fields.Char(string='Time at present location')
    partner_credit_bank_ids = fields.One2many('partner.credit.bank','partner_credit_id',string='Bank Account') 
    trade_reference_ids = fields.One2many('trade.reference','partner_credit_id',string='Bank Account') 
    date = fields.Date(string='Date')
    print_name = fields.Char(string='Print Name')
    signature = fields.Binary(string='Signature')

class TradeReference(models.Model):
    _name = 'trade.reference'
    
    
    name = fields.Char(string='Name')
    address = fields.Char('Street')
    city = fields.Char('City')
    state = fields.Many2one('res.country.state')
    zip = fields.Char('zip')
    phone = fields.Char(string='Phone')
    fax = fields.Char(string='Fax')
    partner_credit_id = fields.Many2one('partner.credit')



class PartnerCreditBank(models.Model):
    _name='partner.credit.bank'

    name = fields.Char(string='Bank')
    acc = fields.Char("Acct. #")
    address = fields.Char('Street')
    city = fields.Char('City')
    state = fields.Many2one('res.country.state')
    zip = fields.Char('zip')

    officer_name = fields.Char(string='Officier Familiar With the account')
    office_phone = fields.Char(string='Phone')
    offier_fax = fields.Char(string='Fax')
    partner_credit_id = fields.Many2one('partner.credit')


class CorporatePartner(models.Model):
    _name='corporate.partner'

    name = fields.Char(string='Name')
    title = fields.Char(string='Title')
    partner_credit_id = fields.Many2one('partner.credit')


 