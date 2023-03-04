import xmlrpc.client
import os, ssl


pwd = 'Confianz^PricePaper379'  # the password of the user
dbname15 = 'pricepaper_v6'  # the reference database

sock15 = xmlrpc.client.ServerProxy('http://127.0.0.65:10070/xmlrpc/2/object')
# dbname15 = "ppt-apps15"  # destination database

# sock15 = xmlrpc.client.ServerProxy('https://apps.pricepaper.com/xmlrpc/2/object')
#

if not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
    ssl._create_default_https_context = ssl._create_unverified_context

for batch in sock15.execute(dbname15, 2, pwd, 'account.batch.payment', 'search_read', [], ['payment_ids', 'name', 'state']):
    for payment in batch.get('payment_ids', []):
        sock15.execute(dbname15, 2, pwd, 'account.payment', 'wrapper_compute_reconciliation', [payment])
        # pass
    batch2 = sock15.execute(dbname15, 2, pwd, 'account.batch.payment', 'read', batch['id'], ['name', 'state'])
    # print(batch2,'\n\n\n', batch)
    if batch['state'] != batch2[0]['state']:
        print(batch['id'],batch['name'],'state changed %s -> %s\n' % (batch['state'], batch2[0]['state']))
