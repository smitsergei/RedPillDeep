from langchain.tools import tool
from core.bybit_client import get_bybit_client
from core.config import Config

client = get_bybit_client()

@tool
def place_order(
    symbol: str, 
    side: str, 
    order_type: str, 
    qty: str, 
    price: str = None, 
    tp: str = None, 
    sl: str = None,
    tpsl_mode: str = "Full",
    position_idx: int = 0
):
    """
    Выставляет ордер на бирже.
    side: 'Buy' или 'Sell'
    order_type: 'Market' или 'Limit'
    tp/sl: цены Take Profit и Stop Loss (устанавливаются сразу с ордером)
    tpsl_mode: 'Full' или 'Partial'
    position_idx: 0 (One-Way), 1 (Hedge Buy), 2 (Hedge Sell)
    """
    try:
        params = {
            "category": "linear",
            "symbol": symbol,
            "side": side,
            "orderType": order_type,
            "qty": str(qty),
            "positionIdx": position_idx,
            "tpslMode": tpsl_mode
        }
        if price and order_type == "Limit":
            params["price"] = str(price)
        
        if tp: params["takeProfit"] = str(tp)
        if sl: params["stopLoss"] = str(sl)

        response = client.place_order(**params)
        if response["retCode"] == 0:
            return f"Ордер успешно размещен: {response['result']['orderId']}"
        return f"Ошибка размещения ордера: {response['retMsg']} (код {response['retCode']})"
    except Exception as e:
        return f"Критическая ошибка при размещении ордера: {e}"

@tool
def set_sl_tp(
    symbol: str, 
    sl: str = None, 
    tp: str = None, 
    tpsl_mode: str = "Full", 
    tp_size: str = None, 
    sl_size: str = None,
    position_idx: int = 0
):
    """
    Устанавливает или обновляет Stop Loss и Take Profit для уже открытой позиции.
    tpsl_mode: 'Full' (на всю позицию) или 'Partial' (частичный)
    tp_size/sl_size: объем для закрытия (обязателен для Partial)
    """
    try:
        params = {
            "category": "linear",
            "symbol": symbol,
            "tpslMode": tpsl_mode,
            "positionIdx": position_idx
        }
        if tp: params["takeProfit"] = str(tp)
        if sl: params["stopLoss"] = str(sl)
        if tp_size: params["tpSize"] = str(tp_size)
        if sl_size: params["slSize"] = str(sl_size)

        response = client.set_trading_stop(**params)
        if response["retCode"] == 0:
            return f"SL/TP успешно обновлен ({tpsl_mode})"
        return f"Ошибка установки SL/TP: {response['retMsg']} (код {response['retCode']})"
    except Exception as e:
        return f"Критическая ошибка SL/TP: {e}"

@tool
def amend_order(
    symbol: str, 
    order_id: str = None, 
    order_link_id: str = None, 
    qty: str = None, 
    price: str = None,
    trigger_price: str = None
):
    """
    Изменяет параметры активного ордера (лимитного или стоп-ордера).
    Нужно указать либо order_id, либо order_link_id.
    """
    try:
        params = {"category": "linear", "symbol": symbol}
        if order_id: params["orderId"] = order_id
        if order_link_id: params["orderLinkId"] = order_link_id
        
        if qty: params["qty"] = str(qty)
        if price: params["price"] = str(price)
        if trigger_price: params["triggerPrice"] = str(trigger_price)

        response = client.amend_order(**params)
        if response["retCode"] == 0:
            return f"Ордер {order_id or order_link_id} успешно изменен"
        return f"Ошибка изменения ордера: {response['retMsg']} (код {response['retCode']})"
    except Exception as e:
        return f"Критическая ошибка при изменении ордера: {e}"

@tool
def cancel_all_symbol_orders(symbol: str = Config.SYMBOL):
    """Отменяет все активные ордера по заданному инструменту."""
    try:
        response = client.cancel_all_orders(category="linear", symbol=symbol)
        if response["retCode"] == 0:
            return "Все ордера отменены"
        return f"Ошибка отмены ордеров: {response['retMsg']} (код {response['retCode']})"
    except Exception as e:
        return f"Критическая ошибка при отмене ордеров: {e}"
