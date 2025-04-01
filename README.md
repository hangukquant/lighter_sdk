# Lighter SDK

The Lighter SDK is a Python library for interacting with the Lighter API, a platform for trading and managing accounts on the Lighter blockchain. This SDK provides a simple and efficient way to access various endpoints, including account management, order placement, market data retrieval, and more.

## Features

- Account management (create, retrieve, and manage accounts)
- Order placement (limit and market orders)
- Market data retrieval (order books, candlesticks, trades, etc.)
- Blockchain data (blocks, transactions, announcements, etc.)
- Easy integration with Python projects

## Installation

To install the Lighter SDK, clone the repository and install the dependencies:

```bash
git clone https://github.com/hangukquant/lighter_sdk
cd lighter_sdk
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the root directory to store your API credentials:

```
LIGHTER_KEY=your_lighter_key
LIGHTER_SECRET=your_lighter_secret
```

## Usage

Here is an example of how to use the Lighter SDK:

```python
import asyncio
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
        price=2.20,
    )
    res = await lighter.market_order(
        ticker='HYPE',
        amount=1,
    )

    res = await lighter.account_active_orders(
        ticker='HYPE',
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
    #...more endpoints!

    await lighter.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

## Examples

Refer to the `examples.py` file for more detailed usage examples, including:

- Placing limit and market orders
- Fetching active and inactive orders
- Retrieving candlestick data
- Accessing exchange statistics

## Official Exchange Docs

The SDK wraps the Lighter API endpoints. For detailed API documentation, visit the [Lighter API Docs](https://apidocs.lighter.xyz).

## Dev
[Dev Contact on X](https://x.com/HangukQuant)
Glady receives donations ETH @ 0xe6cC8516D796051931CE985326Db04E3a5457AFA

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests to improve the SDK.