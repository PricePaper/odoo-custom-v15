# See LICENSE file for full copyright and licensing details.

{
    # Module information
    "name": "RMA-Return Merchandise Authorization Return Exchange Management",
    "version": "15.0.1.0.0",
    "license": 'LGPL-3',
    "category": "Warehouse",
    "summary": "Return merchandise authorization module helps you to manage with product returns and exchanges.",
    "description": '''RMA allows you to process several return functions, such as exchanges, refunds, store credits and return of return.
	RMA can be initiated by the Sale order/Purchase Order or can be initiated by the Picking at any time after an order has been placed.
	Return merchandise authorization module helps
    you to manage with product returns and exchanges.
    Return Merchandise Authorization Return Exchange Management
	rma return material replace exchange product
	Odoo Return Merchandise Authorization
	Return Merchandise Authorization odoo
	Return Merchandise Authorization in odoo
	rma return merchandise authorization
	Return Material Authorization Software
	Return Merchandise Authorization
	return merchandise authorization
	RMA Configurations
	RMA Stock Picking
	RMA Credit Note
	RMA management software
	RMA Invoices
	RMA Portal
	RMA Return goods
	Exchange goods
	Credit notes
	Replace item
	Goods Return Refund
	Exchange
	Payback
	refund
	Return
	Merchandise
	Authorization
	Management
	Exchange
	Odoo RMA
	RMA Odoo
	RMA''',
    
    # Author
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "website": "https://www.serpentcs.com",
    
    # Dependancies
    "depends": ['sale_management', 'sale_stock', 'purchase_stock'],
    
    # Views
    "data": [
            'security/security.xml',
            'security/ir.model.access.csv',
            'data/rma_data.xml',
            'views/res_company.xml',
            'views/rma_view.xml',
            'views/sale_views.xml',
            'views/purchase_views.xml',
            'views/stock_views.xml',
            'report/report_mer_auth_rma.xml',
            'report/rma_report_mer_auth_reg.xml',
            'data/reason_data.xml',
    ],
    
    # Odoo App Store Specific
    "images": ["static/description/Return-Merchandise-Authorization-Return-Exchange-Management-Banner.png"],
    "live_test_url": "https://youtu.be/kqpBZSAGetE",
    
    # Technical
    "installable": True,
    "sequence": 1,
    "price": 53,
    "currency": 'EUR',
    "pre_init_hook": "pre_init_hook",
}
