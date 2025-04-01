import os
import asyncio 
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("LIGHTER_KEY")
secret = os.getenv("LIGHTER_SECRET")

from lighter_sdk.lighter import Lighter
async def main():
    lighter = Lighter(
        key=key,
        secret=secret,
    )
    await lighter.init_client()

    '''actually submits orders'''
    res = await lighter.limit_order(
        ticker='XRP',
        amount=-20,
        price=2.50,
    )
    res = await lighter.market_order(
        ticker='HYPE',
        amount=1,
    )
    res = await lighter.account_active_orders(
        ticker='XRP',
    )
    cancel_order = res['orders'][0]['order_id']
    res = await lighter.cancel_order(
        ticker='XRP',
        order_id=cancel_order,
    )

    res = await lighter.account_orders(
        ticker=24,is_index=True
    )
    
    res = await lighter.orderbook_details(
        ticker='ETH'
    )
    res = await lighter.orderbook_orders(
        ticker=1,is_index=True
    )
    res = await lighter.orderbooks()
    res = await lighter.candlesticks(ticker='HYPE')

    print(await lighter.status())
    print(await lighter.info())
    print(await lighter.account())
    print(await lighter.accounts())
    print(await lighter.accounts_by_l1_address())
    print(await lighter.apikeys())
    print(await lighter.fee_bucket())
    print(await lighter.pnl())
    print(await lighter.public_pools())
    print(await lighter.exchange_stats())
    
    await lighter.cleanup()

if __name__ == "__main__":
    asyncio.run(main())