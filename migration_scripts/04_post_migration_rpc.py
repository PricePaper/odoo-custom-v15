import xmlrpc.client
import os, ssl
import concurrent.futures
import time
import traceback

start = time.strftime("%H:%M:%S", time.localtime())
username = '<user>'  # the user
pwd = 'confianzpricepaper'  # the password of the user
dbname12 = 'pricepaper_v5'  # the reference database
dbname15 = "pricepaper15_v1"  # destination database

# sock12 = xmlrpc.client.ServerProxy('http://127.0.0.65:10010/xmlrpc/2/object')
sock15 = xmlrpc.client.ServerProxy('http://127.0.0.65:10070/xmlrpc/2/object')

# username = 'admin'  # the user
# pwd = 'confianzpricepaper'  # the password of the user
dbname12 = 'ppt_apps1_20220321'  # the reference database
# dbname15 = "ppt-apps15-20220321" # destination database
#
sock12 = xmlrpc.client.ServerProxy('https://odoo-dev.pricepaper.com/xmlrpc/2/object')
# sock15 = xmlrpc.client.ServerProxy('https://odoo-dev15.pricepaper.com/xmlrpc/2/object')
#

res = open("invoice_not_found1.csv", 'a+')
if not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
    ssl._create_default_https_context = ssl._create_unverified_context

field_list = ['discount_date', 'storage_down_payment', 'rma_id', 'invoice_address_id', 'is_storage_contract', 'discount_due_date',
              'check_bounce_invoice']
one2many_fields = {'sale_commission_ids': {'sale.commission': 'invoice_id'}}
many2many_fields = ['sales_person_ids', 'commission_rule_ids']
invoice_line = ['lst_price', 'working_cost', 'is_storage_contract']
limit = 1000
offset = 0
count = sock12.execute(dbname12, 2, pwd, 'account.invoice', 'search_count', [])
sock15.execute(dbname15, 2, pwd, 'ir.config_parameter', 'set_param', 'sequence.mixin.constraint_start_date', '2022-03-28')


# offset = count+10
# while offset <= count:
def update_invoice(offset, limit, domain=[]):
    print(offset, '\n\n\n\n')
    except_id = []
    for invoice in sock12.execute(dbname12, 2, pwd, 'account.invoice', 'search_read', domain, [], offset, limit):
        try:
            domain = False
            if invoice.get('number'):
                domain = [('name', '=', invoice.get('number'))]
            else:
                res.write("%s,%s,'no number'\n" % (invoice.get('id'), invoice.get('number')))
            # print(invoice.get('state'), invoice.get('origin'))
            if invoice.get('state') in ('draft', 'cancel'):
                if invoice.get('origin'):
                    domain = [('invoice_origin', '=', invoice.get('origin'))]
                else:
                    res.write("%s,%s,'no origin'\n" % (invoice.get('id'), invoice.get('number')))
            # print(domain)
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

            if invoice.get('state') in ('draft', 'cancel') and (invoice.get('number') or invoice.get('move_name')):
                sock15.execute(dbname15, 2, pwd, 'account.move', 'set_name_inv', move15['id'], invoice.get('number') or invoice.get('move_name'))
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
        except Exception as e:
            print('\n\n\n-------------------------------%s----------------------\n\n\n' % e)
            traceback.print_exc()
            except_id.append((invoice.get(id)))
    if except_id:
        for e_id in except_id:
            update_invoice(0, None, domain=[('id', '=', e_id)])
    print('\n\nstarts at -------------%s-----------\n\n*****************************stops at %s**********************\n%s\n\n\n' % (
        start, time.strftime("%H:%M:%S", time.localtime()), offset))
    return offset


print('\n\n\n\n*****************************starts at%s**********************\n\n\n\n' % time.strftime("%H:%M:%S", time.localtime()))
executor = concurrent.futures.ProcessPoolExecutor()
for offset in range(0, count, limit):
    print('!!!!!!!!!!!!!!!!!!!!!!!!!!', offset)
    executor.submit(update_invoice, offset, limit)

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
