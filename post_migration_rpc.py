import xmlrpc.client
import os, ssl

username = '<user>'  # the user
pwd = 'confianzpricepaper'  # the password of the user
dbname12 = 'pricepaper_v5'  # the database
dbname15 = "pricepaper15_v1"

sock12 = xmlrpc.client.ServerProxy('http://127.0.0.65:10010/xmlrpc/2/object')
sock15 = xmlrpc.client.ServerProxy('http://127.0.0.65:10070/xmlrpc/2/object')
res = open("invoice_not_found.csv", 'a+')
if not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
    ssl._create_default_https_context = ssl._create_unverified_context

field_list = ['discount_date', 'storage_down_payment', 'rma_id', 'invoice_address_id', 'is_storage_contract', 'discount_due_date',
              'check_bounce_invoice']
one2many_fields = {'sale_commission_ids': {'sale.commission': 'invoice_id'}}
many2many_fields = ['sales_person_ids', 'commission_rule_ids']
invoice_line = ['lst_price', 'working_cost', 'is_storage_contract']
limit = 100
offset = 0
count = sock12.execute(dbname12, 2, pwd, 'account.invoice', 'search_count', [])
sock15.execute(dbname15, 2, pwd, 'ir.config_parameter', 'set_param', 'sequence.mixin.constraint_start_date', '2022-03-28')
offset = count+10
while offset <= count:
    print(offset, '\n\n\n\n')
    for invoice in sock12.execute(dbname12, 2, pwd, 'account.invoice', 'search_read', [],
                  field_list + many2many_fields + ['invoice_line_ids', 'state', 'date', 'name', 'number', 'sale_commission_ids'], offset, limit):
        domain = False
        if invoice.get('number'):
            domain = [('name', '=', invoice.get('number'))]
        else:
            res.write("%s,%s,'no number'\n" % (invoice.get('id'), invoice.get('number')))
        if invoice.get('state') in ('draft', 'cancel'):
            if invoice.get('origin'):
                domain = [('invoice_origin', '=', invoice.get('origin'))]
            else:
                res.write("%s,%s,'no origin'\n" % (invoice.get('id'), invoice.get('number')))
        print(domain)
        if not domain:
            continue
        move15 = sock15.execute(dbname15, 2, pwd, 'account.move', 'search_read', domain, [])
        # print(move15)
        if not move15:
            res.write("%s,%s,'missing'\n" % (invoice.get('id'), invoice.get('number')))
            continue
        if len(move15) > 1:
            tmp = False
            for move in move15:
                if invoice['state'] == move['state'] and invoice['amount_total'] == move['amount_total']:
                    tmp = move
                    break
            res.write("%s,%s,'duplicate_found'\n" % (invoice.get('id'), invoice.get('number')))
            if tmp:
                move15 = tmp
            else:
                res.write("%s,%s,'can't handle manual operation needed'\n" % (invoice.get('id'), invoice.get('number')))
                break
        else:
            move15 = move15[0]
        vals = {}
        for field in field_list:
            if invoice.get(field) is not None:
                vals.update({field: invoice.get(field)})
                if isinstance(invoice.get(field), list) and len(invoice.get(field)) > 0:
                    vals.update({field: invoice.get(field)[0]})

        for field in many2many_fields:
            vals.update({field: [(6, 0, invoice.get(field))]})

        if invoice.get('state') in ('draft', 'cancel'):
            vals.update({'name': invoice.get('number') or invoice.get('move_name')})
        # if invoice['date'] != move15['date']:
        #     vals.update({'date': invoice['date']})
        sock15.execute(dbname15, 2, pwd, 'account.move', 'write', move15['id'], vals)
        for field in one2many_fields:
            if invoice[field]:
                for model in one2many_fields[field]:
                    sock15.execute(dbname15, 2, pwd, model, 'write', invoice[field], {one2many_fields[field][model]: move15['id']})
        move_line = sock15.execute(dbname15, 2, pwd, 'account.move.line', 'read', move15.get('invoice_line_ids'))
        for line in sock12.execute(dbname12, 2, pwd, 'account.invoice.line', 'read', invoice.get('invoice_line_ids')):
            line_vals = {}
            for field in invoice_line:
                if line.get(field) is not None:
                    line_vals.update({field: line.get(field)})
            if line_vals:
                for l in move_line:
                    if l.get('name') == line.get('name') and l.get('quantity') == line.get('quantity') and l.get('sub_total') == line.get(
                            'sub_total'):
                        sock15.execute(dbname15, 2, pwd, 'account.move.line', 'write', l['id'], line_vals)
    offset += limit
res.close()
for field in ['refund_qty', 'order_quantity', 'delivered_quantity', 'total_qty']:
    sock15.execute(dbname15, 2, pwd, 'rma.ret.mer.auth', 'set_filed_value', field)
for account_type in sock15.execute(dbname15, 2, pwd, 'account.account.type', 'search_read', [['internal_group', '=', False]]):
    vals = {}
    if 'Asset' in account_type.get('name'):
        vals = {'internal_group': 'asset'}
    elif 'Liabilities' in account_type.get('name'):
        vals = {'internal_group': 'liability'}
    elif 'Expenses' in account_type.get('name'):
        vals = {'internal_group': 'expense'}
    if vals:
        sock15.execute(dbname15, 2, pwd, 'account.account.type', 'write', account_type['id'], vals)
sock15.execute(dbname15, 2, pwd, 'sale.order', 'activate_views', [])
print("Done")
