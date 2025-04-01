import time
import asyncio 
import logging

from datetime import datetime
from lighter import SignerClient
from lighter_sdk.httpx import HTTPClient

logging.basicConfig(level=logging.INFO)

BASE_URL = "https://mainnet.zklighter.elliot.ai"
CHAIN_ID_MAINNET = 304

endpoints = {
    #https://apidocs.lighter.xyz/reference/status (root)
    'status':{
        "endpoint":"/",
        "method":"GET",
    },
    'info':{
        "endpoint":"/info",
        "method":"GET",
    },

    #https://apidocs.lighter.xyz/reference/account-1 (account)
    'account':{
        "endpoint": "/api/v1/account",
        "method": "GET",
    },
    'accounts':{
        "endpoint": "/api/v1/accounts",
        "method": "GET",
    },
    'accounts_by_l1_address':{
        "endpoint":"/api/v1/accountsByL1Address",
        "method":"GET",
    },
    'apikeys':{
        "endpoint": "/api/v1/apikeys",
        "method": "GET",
    },
    'fee_bucket':{
        "endpoint": "/api/v1/feeBucket",
        "method": "GET",
    },
    'pnl':{
        "endpoint": "/api/v1/pnl",
        "method": "GET",
    },
    'public_pools':{
        "endpoint": "/api/v1/publicPools",
        "method": "GET",
    },

    #(order)
    'account_active_orders':{
        "endpoint": "/api/v1/accountActiveOrders",
        "method": "GET",
    },
    'account_inactive_orders':{
        "endpoint": "/api/v1/accountInactiveOrders",
        "method": "GET",
    }, #TODO
    'account_orders':{
        "endpoint": "/api/v1/accountOrders",
        "method": "GET",
    },
    "limit_order":{}, #see implementation
    "cancel_order":{}, #see implementation

    'exchange_stats':{
        "endpoint": "/api/v1/exchangeStats",
        "method": "GET",
    },
    'orderbook_details':{
        "endpoint": "/api/v1/orderBookDetails",
        "method": "GET",
    },
    'orderbook_orders':{
        "endpoint": "/api/v1/orderBookOrders",
        "method": "GET",
    },
    'orderbooks':{
        'endpoint': "/api/v1/orderBooks",
        'method': "GET",
    },
    'recent_trades':{
        'endpoint': "/api/v1/recentTrades",
        'method': "GET",
    },
    'trades':{
        'endpoint': "/api/v1/trades",
        'method': "GET",
    },

    
    #https://apidocs.lighter.xyz/reference/accounttxs (transaction)
    
    #https://mainnet.zklighter.elliot.ai/api/v1/accountTxs
    'accounttxs':{
        "endpoint": "/api/v1/accountTxs",
        "method": "GET",
    },
    'blocktxs':{
        "endpoint": "/api/v1/blockTxs",
        "method": "GET",
    },
    'deposit_history': {},
    'next_nonce': {
        "endpoint": "/api/v1/nextNonce",
        "method": "GET",
    },
    'send_tx': {
        "endpoint": "/api/v1/sendTx",
        "method": "POST",
    }, #see limit order, cancel order etc (order actions)
    'send_tx_batch': {
        "endpoint": "/api/v1/sendTxBatch",
        "method": "POST",
    }, #TODO

    'tx':{
        "endpoint": "/api/v1/tx",
        "method": "GET",
    },
    'tx_from_l1_txhash':{
        "endpoint": "/api/v1/txFromL1TxHash",
        "method": "GET",
    },
    'txs':{
        "endpoint": "/api/v1/txs",
        "method": "GET",
    },
    'withdraw_history':{
        "endpoint": "/api/v1/withdrawHistory",
        "method": "GET",
    },

    #https://apidocs.lighter.xyz/reference/announcement-1 (announcement)
    'announcement':{
        "endpoint": "/api/v1/announcement",
        "method": "GET",
    },

    #https://apidocs.lighter.xyz/reference/blocks (block)
    'block': {
        "endpoint": "/api/v1/block",
        "method": "GET",
    },
    'blocks':{
        "endpoint": "/api/v1/blocks",
        "method": "GET",
    },
    'current_height':{
        "endpoint": "/api/v1/currentHeight",
        "method": "GET",
    },

    #https://apidocs.lighter.xyz/reference/candlesticks (candlestick)
    'fundings':{
        "endpoint": "/api/v1/fundings",
        "method": "GET",
    },
    'candlesticks':{
        "endpoint": "/api/v1/candlesticks",
        "method": "GET",
    },

    #https://apidocs.lighter.xyz/reference/layer2basicinfo (info)
    'layer2BasicInfo':{
        "endpoint": "/api/v1/layer2BasicInfo",
        "method": "GET",
    },
}

class Lighter():
    
    def __init__(self,key=None,secret=None):
        self.key = key
        self.secret = secret
        self.http_client = HTTPClient(base_url=BASE_URL)

        self.aws_manager = None
        self.state_manager = None

        self.positions = None 
        self.orders = None 
        self.l2_dict = {}
        self.l2_update = {}

        self.shutdown = False
        return

    async def init_client(self):
        self.client = SignerClient(
            url=BASE_URL,
            private_key=self.secret,
            chain_id=CHAIN_ID_MAINNET
        )

        account_created = False
        new_account = False
        while not account_created:
            try:
                await self.client.set_account_index()
                account_created = True
                if new_account:
                    await asyncio.sleep(5)
            except Exception as e:
                new_account = True
                print("Account not created yet")
            time.sleep(1)

        main = await self.accounts_by_l1_address()
        self.account_idx = main['sub_accounts'][0]['index']
        ticker_meta = await self.orderbooks()
        orderbooks = ticker_meta['order_books']
        
        ticker_to_idx = {}
        ticker_to_price_precision = {}
        ticker_to_lot_precision = {}
        ticker_min_base = {}
        ticker_min_quote = {}

        for ticker in orderbooks:
            ticker_to_idx[ticker['symbol']] = int(ticker['market_id'])
            ticker_to_price_precision[ticker['symbol']] = int(ticker['supported_price_decimals'])
            ticker_to_lot_precision[ticker['symbol']] = int(ticker['supported_size_decimals'])
            ticker_min_base[ticker['symbol']] = float(ticker['min_base_amount'])
            ticker_min_quote[ticker['symbol']] = float(ticker['min_quote_amount'])

        self.idx_to_ticker = {v:k for k,v in ticker_to_idx.items()}
        self.ticker_to_idx = ticker_to_idx
        self.ticker_to_price_precision = ticker_to_price_precision
        self.ticker_to_lot_precision = ticker_to_lot_precision
        self.ticker_min_base = ticker_min_base
        self.ticker_min_quote = ticker_min_quote

    async def cleanup(self):
        await self.http_client.cleanup()
        await self.client.close()

    async def limit_order(
        self,
        ticker,
        amount,
        price,
        tif='GTC',
        client_order_index=0,
        is_index=False,
        reduce_only=False,
        **kwargs
    ): 
        if tif == 'GTC': tif = 1
        elif tif == 'IOC': tif = 0
        elif tif == 'ALO': tif = 2
        market_id = self.ticker_to_idx[ticker] if not is_index else ticker
        is_ask = False if amount > 0 else True
        price = round(price * 10**self.ticker_to_price_precision[ticker])
        if abs(amount) < self.ticker_min_base[ticker]:
            raise ValueError(f"Minimum base amount for {ticker} is {self.ticker_min_base[ticker]}")
        
        base_amount = round(abs(amount) * 10**self.ticker_to_lot_precision[ticker])
        return await self.client.create_order(
            market_index=market_id,
            client_order_index=client_order_index,
            base_amount=base_amount,
            price=price,
            is_ask=is_ask,
            order_type=0, #ORDER_TYPE_LIMIT
            time_in_force=tif,
            reduce_only=int(reduce_only),
            trigger_price=0
        )

    async def market_order(
        self,
        ticker,
        amount,
        tif='GTC',
        reduce_only=False,
        slippage_tolerance=0.03,
        is_index=False,
        **kwargs
    ):
        market_id = self.ticker_to_idx[ticker] if not is_index else ticker
        lob = await self.orderbook_orders(market_id,is_index=True)
        bids = lob['bids']
        asks = lob['asks']
        bb = float(bids[0]['price'])
        aa = float(asks[0]['price'])
        price = (bb + aa) / 2
        is_long = True if amount > 0 else False
        price *= (1 + slippage_tolerance) if is_long else (1 - slippage_tolerance)
        return await self.limit_order(
            ticker=ticker,
            amount=amount,
            price=price,
            tif=tif,
            reduce_only=reduce_only,
            is_index=is_index,
            **kwargs
        )

    async def cancel_order(self,ticker,order_id,is_index=False):
        market_id = self.ticker_to_idx[ticker] if not is_index else ticker
        return await self.client.cancel_order(
            market_index=market_id,
            order_index=int(order_id)
        )
        
    async def status(self):
        endpoint = dict(endpoints['status'])
        return await self.http_client.request(
            **endpoint,
            params={}
        )

    async def info(self):
        endpoint = dict(endpoints['info'])
        return await self.http_client.request(
            **endpoint,
            params={}
        )

    async def account(self,by='l1_address',value=None):
        endpoint = dict(endpoints['account'])
        account_idx = self.account_idx
        endpoint['params'] = {
            'by':by,
            'value':self.key if by == 'l1_address' else account_idx
        }
        return await self.http_client.request(
            **endpoint,
        )

    async def accounts(self,limit=100,**kwargs):
        endpoint = dict(endpoints['accounts'])
        endpoint['params'] = {
            'limit':limit,
            **kwargs
        }
        return await self.http_client.request(
            **endpoint,
        )

    async def accounts_by_l1_address(self):
        '''
        account index > integer used by lighter to identify wallet
        sub_accounts[0] > your main account, sub_accounts[0]['index'] is your account index.
        '''
        endpoint = dict(endpoints['accounts_by_l1_address'])
        endpoint['params'] = {
            'l1_address':self.key
        }
        return await self.http_client.request(
            **endpoint,
        )   

    async def apikeys(self,account_idx=None,api_key_index=255):
        account_idx = account_idx or self.account_idx
        endpoint = dict(endpoints['apikeys'])
        endpoint['params'] = {
            'account_index':account_idx,
            'api_key_index':api_key_index
        }
        return await self.http_client.request(
            **endpoint,
        )
        
    async def fee_bucket(self,account_idx=None):
        account_idx = account_idx or self.account_idx
        endpoint = dict(endpoints['fee_bucket'])
        endpoint['params'] = {
            'account_index':account_idx
        }
        return await self.http_client.request(
            **endpoint,
        )
    
    async def pnl(self,by="index",account_idx=None,start=None,end=None,resolution='1h',count_back=2,**kwargs):
        value = account_idx or self.account_idx
        start = start or int(datetime.now().timestamp() - 60 * 60 * 24)
        end = end or int(datetime.now().timestamp())
        endpoint = dict(endpoints['pnl'])
        endpoint['params'] = {
            'by':by,
            'value':value,
            'resolution':resolution,
            'start_timestamp':start,
            'end_timestamp':end,
            'count_back':count_back,
            **kwargs
        }
        return await self.http_client.request(
            **endpoint,
        )

    async def public_pools(self,index=0,limit=100,**kwargs):
        endpoint = dict(endpoints['public_pools'])
        endpoint['params'] = {
            'index':index,
            'limit':limit,
            **kwargs
        }
        return await self.http_client.request(
            **endpoint,
        )
    
    async def account_active_orders(self,ticker,account_idx=None,is_index=False,**kwargs):
        account_idx = account_idx or self.account_idx
        endpoint = dict(endpoints['account_active_orders'])
        market_id = self.ticker_to_idx[ticker] if not is_index else ticker
        endpoint['params'] = {
            'account_index':account_idx,
            'market_id':market_id,
            'auth':self.client.create_auth_token_with_expiry(
                SignerClient.DEFAULT_10_MIN_AUTH_EXPIRY
            )
        }
        return await self.http_client.request(
            **endpoint,
        )

    async def account_orders(self,ticker,account_idx=None,cursor=None,is_index=False,limit=100):
        market_id = self.ticker_to_idx[ticker] if not is_index else ticker 
        account_idx = account_idx or self.account_idx    
        endpoint = dict(endpoints['account_orders'])
        endpoint['params'] = {
            'account_index':account_idx,
            'market_id':market_id,
            'limit':limit
        }
        if cursor:
            endpoint['params']['cursor'] = cursor
        return await self.http_client.request(
            **endpoint,
        )

    async def exchange_stats(self):
        endpoint = dict(endpoints['exchange_stats'])
        return await self.http_client.request(
            **endpoint,
        )

    async def orderbook_details(self,ticker=None,is_index=False):
        endpoint = dict(endpoints['orderbook_details'])
        if ticker is not None:
            market_id = self.ticker_to_idx[ticker] if not is_index else ticker
            endpoint['params'] = {'market_id':market_id}
        return await self.http_client.request(
            **endpoint,
        )

    async def orderbook_orders(self,ticker,limit=100,is_index=False,**kwargs):
        endpoint = dict(endpoints['orderbook_orders'])
        market_id = self.ticker_to_idx[ticker] if not is_index else ticker
        endpoint['params'] = {
            'market_id':market_id,
            'limit':limit,
            **kwargs
        }
        return await self.http_client.request(
            **endpoint,
        )

    async def orderbooks(self,ticker=None,is_index=False):
        endpoint = dict(endpoints['orderbooks'])
        if ticker is not None:
            market_id = self.ticker_to_idx[ticker] if not is_index else ticker
            endpoint['params'] = {'market_id':market_id}
        return await self.http_client.request(
            **endpoint,
        )

    async def recent_trades(self,ticker,limit=100,is_index=False,**kwargs):
        endpoint = dict(endpoints['recent_trades'])
        market_id = self.ticker_to_idx[ticker] if not is_index else ticker
        endpoint['params'] = {
            'market_id':market_id,
            'limit':limit,
            **kwargs
        }
        return await self.http_client.request(
            **endpoint,
        )
    
    async def trades(self,ticker=None,limit=100,sort_by='timestamp',is_index=False,**kwargs):
        endpoint = dict(endpoints['trades'])
        endpoint['params'] = {
            'limit':limit,
            'sort_by':sort_by,
            **kwargs
        }
        if ticker is not None:
            market_id = self.ticker_to_idx[ticker] if not is_index else ticker
            params.update({'market_id':market_id})
        return await self.http_client.request(
            **endpoint,
        )

    async def accounttxs(self,account_idx=None,by='account_index',limit=100,**kwargs):
        account_idx = account_idx or self.account_idx
        endpoint = dict(endpoints['accounttxs'])
        endpoint['params'] = {
            'by':by,
            'value':account_idx,
            'limit':limit,
            **kwargs
        }
        return await self.http_client.request(
            **endpoint,
        )

    async def blocktxs(self,commitment=None,height=None):
        endpoint = dict(endpoints['blocktxs'])
        endpoint['params'] = {
            'by':'block_commitment' if commitment else 'block_height',
            'value':commitment or height
        }
        return await self.http_client.request(
            **endpoint,
        )

    async def deposit_history(self,**kwargs):
        pass 
    
    async def next_nonce(self,account_idx=None,api_key_index=0):
        account_idx = account_idx or self.account_idx
        endpoint = dict(endpoints['next_nonce'])
        endpoint['params'] = {
            'account_index':account_idx,
            'api_key_index':api_key_index
        }
        return await self.http_client.request(
            **endpoint,
        )

    async def tx(self):
        pass 
    
    async def tx_from_l1_txhash(self):
        pass 
    
    async def txs(self):
        pass
    
    async def withdraw_history(self):
        pass

    async def announcement(self):
        endpoint = dict(endpoints['announcement'])
        return await self.http_client.request(
            **endpoint,
        )

    async def block(self,commitment=None,height=None):
        endpoint = dict(endpoints['block'])
        endpoint['params'] = {
            'by':'commitment' if commitment else 'height',
            'value':commitment or height
        }
        return await self.http_client.request(
            **endpoint,
        )

    async def blocks(self,limit=100,**kwargs):
        endpoint = dict(endpoints['blocks'])
        endpoint['params'] = {
            'limit':limit,
            **kwargs
        }
        return await self.http_client.request(
            **endpoint,
        )

    async def current_height(self):  
        endpoint = dict(endpoints['current_height'])
        return await self.http_client.request(
            **endpoint,
        )

    async def fundings(self,ticker,resolution='1h',start=None,end=None,count_back=2,is_index=False,**kwargs):
        market_id = self.ticker_to_idx[ticker] if not is_index else ticker
        start = start or int(datetime.now().timestamp() - 60 * 60 * 24)
        end = end or int(datetime.now().timestamp())
        endpoint = dict(endpoints['fundings'])
        endpoint['params'] = {
            'market_id':market_id,
            'resolution':resolution,
            'start_timestamp':start,
            'end_timestamp':end,
            'count_back':count_back,
            **kwargs
        }
        return await self.http_client.request(
            **endpoint,
        )

    async def candlesticks(self,ticker,resolution='1h',start=None,end=None,count_back=2,set_timestamp_to_end=False,is_index=False,**kwargs):
        market_id = self.ticker_to_idx[ticker] if not is_index else ticker
        start = start or int(datetime.now().timestamp() - 60 * 60 * 24)
        end = end or int(datetime.now().timestamp())
        endpoint = dict(endpoints['candlesticks'])
        endpoint['params'] = {
            'market_id':market_id,
            'resolution':resolution,
            'start_timestamp':start,
            'end_timestamp':end,
            'count_back':count_back,
            'set_timestamp_to_end':set_timestamp_to_end,
            **kwargs
        }
        return await self.http_client.request(
            **endpoint,
        )

    async def layer2BasicInfo(self):
        endpoint = dict(endpoints['layer2BasicInfo'])
        return await self.http_client.request(
            **endpoint,
        )
