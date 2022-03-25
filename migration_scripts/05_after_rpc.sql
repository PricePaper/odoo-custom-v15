UPDATE account_move SET sequence_prefix = concat(split_part(name, '/',1),'/', split_part(name, '/',2), '/'),
sequence_number = CAST(split_part(name, '/',3) AS INTEGER)
WHERE name != '/' and move_type != 'entry' and length(name)>10 and position('/' in name) > 2;
