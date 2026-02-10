from langchain.tools import tool
from core.bybit_client import get_bybit_client
from core.config import Config

client = get_bybit_client()

@tool
def place_order(symbol: str, side: str, order_type: str, qty: str, price: str = None):
    """
    Выставляет ордер на бирже.
    side: 'Buy' или 'Sell'
    order_type: 'Market' или 'Limit'
    """
    params = {
        "category": "linear",
        "symbol": symbol,
        "side": side,
        "orderType": order_type,
        "qty": qty,
    }
    if price and order_type == "Limit":
        params["price"] = price

    response = client.place_order(**params)
    if response["retCode"] == 0:
        return f"Ордер успешно размещен: {response['result']['orderId']}"
    return f"Ошибка размещения ордера: {response['retMsg']}"

@tool
def set_sl_tp(symbol: str, sl: str = None, tp: str = None):
    """Устанавливает Stop Loss и Take Profit для открытой позиции."""
    params = {
        "category": "linear",
        "symbol": symbol,
    }
    if sl: params["stopLoss"] = sl
    if tp: params["takeProfit"] = tp

    response = client.set_trading_stop(**params)
    if response["retCode"] == 0:
        return "SL/TP успешно обновлены"
    return f"Ошибка установки SL/TP: {response['retMsg']}"

@tool
def cancel_all_symbol_orders(symbol: str = Config.SYMBOL):
    """Отменяет все активные ордера по заданному инструменту."""
    response = client.cancel_all_orders(category="linear", symbol=symbol)
    if response["retCode"] == 0:
        return "Все ордера отменены"
    return f"Ошибка отмены ордеров: {response['retMsg']}"
