from pybit.unified_trading import HTTP
from core.config import Config

def get_bybit_client():
    return HTTP(
        testnet=Config.BYBIT_TESTNET,
        api_key=Config.BYBIT_API_KEY,
        api_secret=Config.BYBIT_API_SECRET,
    )
