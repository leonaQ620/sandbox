from pandas.core.indexes.base import Index
from tornado import web,httpserver,ioloop
from urllib.error import HTTPError
from algosdk.error import IndexerHTTPError
import pandas as pd
import numpy as np
# account_info.py
import json
# requires Python SDK version 1.3 or higher
from algosdk.v2client import indexer

myindexer = indexer.IndexerClient(indexer_token="", indexer_address='http://localhost:8980')

def address_input(address):    
    response_account_info = myindexer.account_info(address = address)
    response_search_transactions_by_address = myindexer.search_transactions_by_address(address =address)
    return response_account_info, response_search_transactions_by_address

#TxID search
def TxID_input(txid):
    response_transaction = myindexer.transaction(txid = txid)
    return response_transaction

#block search
def block_input(block):
    response_block_info = myindexer.block_info(block = block)
    return response_block_info

#asset name search
def asset_name_input(asset_name):
    response_search_assets = myindexer.search_assets(name = asset_name)
    return response_search_assets

#asset id search
def asset_id_input(asset_id):
    #response_accounts = myindexer.accounts(asset_id = asset_id)
    #response_asset_balances = myindexer.asset_balances(asset_id = asset_id)
    #response_search_asset_transactions = myindexer.search_asset_transactions(asset_id = asset_id)
    #response_search_assets = myindexer.search_assets(asset_id = asset_id)
    response_asset_info = myindexer.asset_info(asset_id = asset_id)
    return response_asset_info

#app id search
def app_id_input(app_id):    
    response_applications = myindexer.applications(application_id = app_id)
    response_search_applications = myindexer.search_applications(application_id = app_id)
    return json.dumps(response_applications, indent = 2, sort_keys = True), \
            json.dumps(response_search_applications, indent = 2, sort_keys = True)

def sparse_search(search_keywords):
    # identify Address / TxID / Group TxID / Block / Asset Name/ AssetID / App ID
    try:
        res = address_input(address=search_keywords)
        tp = 'account'
    except (HTTPError,IndexerHTTPError):
        try: 
            res = TxID_input(txid = search_keywords)
            tp = 'trans'
        except (HTTPError,IndexerHTTPError):
            try:
                res = (asset_id_input(asset_id = search_keywords), block_input(block = search_keywords))
                tp = 'asset_id'
            except (HTTPError,IndexerHTTPError):
                try: 
                    res = asset_name_input(asset_name = search_keywords)
                    tp = 'asset_n'
                    if res['assets'] == []:
                        raise TypeError
                except (TypeError):
                    try: 
                        res = block_input(block = search_keywords)
                        tp = 'block'
                    except (HTTPError,IndexerHTTPError):
                        try:
                            res = app_id_input(app_id=search_keywords)
                            tp = 'app'
                        except (HTTPError,IndexerHTTPError):
                            res = 'ERROR: invalidate input'
    return (res,tp)

def result(res):
    if res[1] == 'account':
        return '/info'
    elif res[1] == 'trans':
        return '/trans'
    elif res[1] == 'block':
        return '/block'
    elif res[1] == 'asset_n':
        return '/asset_n'
    elif res[1] == 'asset_id':
        return '/asset_id'
    elif res[1] == 'app':
        return '/app'
    else:
        return '/ERROR'

def clean_account_info(respond):
    add = respond[0]['account']['address']
    amount = respond[0]['account']['amount']
    curr_round = respond[0]['account']['round']
    rewards = respond[0]['account']['rewards']
    pending_rewards = respond[0]['account']['pending-rewards']
    status = respond[0]['account']['status']
    trans_round = []
    trans_id = []
    trans_from = []
    trans_to = []
    trans_amount = []
    trans_time = []
    num = []
    i = 0
    for trans in respond[1]['transactions']:
        trans_round.append(trans['confirmed-round'])
        trans_id.append(trans['id'])
        trans_from.append(trans['sender'])
        trans_to.append(trans['payment-transaction']['receiver'])
        trans_amount.append(trans['payment-transaction']['amount'])
        trans_time.append((curr_round - trans['confirmed-round'])*4)
        i+=1
        num.append(i)
    output_account = {'Address Information':add,'ALGO BALANCE':amount,
                      'ROUND LAST SEEN':curr_round,'REWARDS':rewards,
                      'PENDING REWARDS':pending_rewards,'STATUS':status}
    output_trans = pd.DataFrame({'#': num, 'ROUND': trans_round, 'TX_ID': trans_id,
                                 'FROM': trans_from, 'TO': trans_to, 'AMOUNT': trans_amount, 
                                 'TIME': trans_time})
    return output_account, output_trans

class MainHanlder(web.RequestHandler):
    def get(self):
        self.render('index.html')
    """def post(self):
        print("GOT  YOUUUUUUUUUUUUUUUU")
        host=self.get_argument("host")
        address=self.get_argument("address")
        #print(host)
        myindexer = indexer.IndexerClient(indexer_token="", indexer_address=host)
        judge = result(sparse_search(search_keywords=address))
        print(judge)

        #self.write(response)
        #self.write(response1)
        #self.write(response2)
        self.redirect(judge)"""
    

"""class IndexHanlder(web.RequestHandler):
    def post(self):
        print("GOT  YOUUUUUUUUUUUUUUUU")
        host=self.get_argument("host")
        address=self.get_argument("address")
        #print(host)
        myindexer = indexer.IndexerClient(indexer_token="", indexer_address=host)
        judge = result(sparse_search(search_keywords=address))
        print(judge)

        #self.write(response)
        #self.write(response1)
        #self.write(response2)
        self.redirect(judge)"""

class AccountHanlder(web.RequestHandler):
    def post(self):
        print('NO2222222222222')
        host=self.get_argument("host")
        address=self.get_argument("address")
        #print(host)
        myindexer = indexer.IndexerClient(indexer_token="", indexer_address=host)

        judge = result(sparse_search(search_keywords=address))

        if judge == '/info':
            response = clean_account_info(sparse_search(search_keywords=address)[0])[1].to_html(index=False)
            response1 = clean_account_info(sparse_search(search_keywords=address)[0])[0]
            
            #self.write(response1)
            #self.write(response2)
            self.render('info.html',response = response, response1 = response1)
        elif judge == '/trans':
            response = sparse_search(search_keywords=address)[0]
            #self.write(response1)
            #self.write(response2)
            self.render('trans.html',response = response)
        elif judge == '/block':
            response = sparse_search(search_keywords=address)[0]
            #self.write(response1)
            #self.write(response2)
            self.render('block.html',response = response)
        elif judge == '/asset_n':
            response = sparse_search(search_keywords=address)[0]
            #self.write(response1)
            #self.write(response2)
            self.render('asset_n.html',response = response)
        elif judge == '/asset_id':
            response = sparse_search(search_keywords=address)[0]
            #self.write(response1)
            #self.write(response2)
            self.render('asset_id.html',response = response)
        elif judge == '/app':
            response = sparse_search(search_keywords=address)[0]
            #self.write(response1)
            #self.write(response2)
            self.render('app.html',response = response)
    
class TransHanlder(web.RequestHandler):
    def post(self):
        host=self.get_argument("host")
        address=self.get_argument("address")
        #print(host)
        myindexer = indexer.IndexerClient(indexer_token="", indexer_address=host)
        response = sparse_search(search_keywords=address)[0]
        
        #self.write(response1)
        #self.write(response2)
        self.render('trans.html',response = response)




#search engine
# class create(web.RequestHandler):
#     def post(self):
#         host=self.get_argument('host')
#         address=self.get_argument('address')
#
#         print(host)
#
#         myindexer = indexer.IndexerClient(indexer_token="", indexer_address=host)
#
#         response = myindexer.account_info(address=address)
#
#
#
#         self.render('info.html',response)



application = web.Application([
            (r"/", MainHanlder),
            (r'/info',AccountHanlder),
            (r'/trans',TransHanlder)])

if __name__ == '__main__':

        http_server = httpserver.HTTPServer(application)
        http_server.listen(8080)
        ioloop.IOLoop.current().start()