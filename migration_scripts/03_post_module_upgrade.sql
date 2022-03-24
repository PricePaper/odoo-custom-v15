update res_partner set customer=customer_ppt,supplier=supplier_ppt;
update account_move set name=inv_number where state in ('draft', 'cancel') and inv_number is not null and move_type != 'entry';
