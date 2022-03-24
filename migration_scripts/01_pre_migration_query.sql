update ir_rule set domain_force='["|", ("type", "!=", "private"), ("type", "=", False)]' where name= 'res.partner.rule.private.employee';
ALTER TABLE res_partner
ADD COLUMN customer_ppt BOOLEAN,
ADD COLUMN supplier_ppt BOOLEAN;
UPDATE res_partner SET customer_ppt=customer, supplier_ppt=supplier;
ALTER TABLE account_invoice
ADD COLUMN inv_number VARCHAR;
UPDATE account_invoice SET inv_number=number where number is not null;
