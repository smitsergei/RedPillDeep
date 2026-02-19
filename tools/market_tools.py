import pandas as pd
import numpy as np
from langchain.tools import tool
from core.bybit_client import get_bybit_client
from core.config import Config

client = get_bybit_client()

@tool
def get_klines(symbol: str = Config.SYMBOL, interval: str = "15", limit: int = 20):
    """Получает последние свечи для анализа краткосрочной динамики (RSI, EMA, Price Action)."""
    try:
        response = client.get_kline(
            category="linear",
            symbol=symbol,
            interval=interval,
            limit=limit
        )
        if response["retCode"] == 0:
            return response["result"]["list"]
        return f"Ошибка Bybit (retCode {response['retCode']}): {response['retMsg']}"
    except Exception as e:
        return f"Критическая ошибка при получении свечей: {e}"

@tool
def get_ticker_price(symbol: str = Config.SYMBOL):
    """Получает текущую цену инструмента."""
    try:
        response = client.get_tickers(category="linear", symbol=symbol)
        if response["retCode"] == 0:
            return response["result"]["list"][0]["lastPrice"]
        return f"Ошибка Bybit (retCode {response['retCode']}): {response['retMsg']}"
    except Exception as e:
        return f"Критическая ошибка при цены: {e}"

@tool
def get_open_positions():
    """Возвращает список текущих открытых позиций по всем символам."""
    try:
        response = client.get_positions(category="linear", settleCoin="USDT")
        if response["retCode"] == 0:
            # Фильтруем только активные позиции
            active = [p for p in response["result"]["list"] if float(p["size"]) > 0]
            return active
        return f"Ошибка Bybit (retCode {response['retCode']}): {response['retMsg']}"
    except Exception as e:
        return f"Критическая ошибка при получении позиций (проверьте API ключи): {e}"

@tool
def get_instrument_info(symbol: str = Config.SYMBOL):
    """Возвращает правила торговли: точность цены (tickSize) и минимальный объем (qtyStep)."""
    try:
        response = client.get_instruments_info(category="linear", symbol=symbol)
        if response["retCode"] == 0:
            info = response["result"]["list"][0]
            return {
                "symbol": info["symbol"],
                "tickSize": info["priceFilter"]["tickSize"],
                "qtyStep": info["lotSizeFilter"]["qtyStep"],
                "minOrderQty": info["lotSizeFilter"]["minOrderQty"],
                "maxOrderQty": info["lotSizeFilter"]["maxOrderQty"]
            }
        return f"Ошибка Bybit: {response['retMsg']}"
    except Exception as e:
        return f"Критическая ошибка при получении инфо об инструменте: {e}"

@tool
def calculate_technical_indicators(symbol: str = Config.SYMBOL):
    """Рассчитывает недельные и дневные уровни Pivot, а также Z-Score для анализа тренда и входов."""
    try:
        # 1. Недельные Pivot (W) - для определения глобального тренда
        resp_w = client.get_kline(category="linear", symbol=symbol, interval="W", limit=2)
        weekly_pivot_data = {}
        if resp_w["retCode"] == 0 and len(resp_w["result"]["list"]) >= 2:
            # Прошлая неделя: [startTime, open, high, low, close, ...]
            last_w = resp_w["result"]["list"][1]
            wh, wl, wc = float(last_w[2]), float(last_w[3]), float(last_w[4])
            wp = (wh + wl + wc) / 3
            weekly_pivot_data = {
                "pivot": round(wp, 2),
                "r1": round((2 * wp) - wl, 2),
                "s1": round((2 * wp) - wh, 2),
                "high": wh,
                "low": wl
            }

        # 2. Дневные Pivot (D) - для торговли внутри дня
        resp_d = client.get_kline(category="linear", symbol=symbol, interval="D", limit=2)
        daily_pivot_data = {}
        if resp_d["retCode"] == 0 and len(resp_d["result"]["list"]) >= 2:
            last_d = resp_d["result"]["list"][1]
            dh, dl, dc = float(last_d[2]), float(last_d[3]), float(last_d[4])
            dp = (dh + dl + dc) / 3
            dr1 = (2 * dp) - dl
            ds1 = (2 * dp) - dh
            
            # Расчет стоп-уровней (промежуточных значений)
            daily_pivot_data = {
                "pivot": round(dp, 2),
                "r1": round(dr1, 2),
                "s1": round(ds1, 2),
                "mid_r1": round((dp + dr1) / 2, 2), # Уровень между P и R1
                "mid_s1": round((dp + ds1) / 2, 2), # Уровень между P и S1
                "high": dh,
                "low": dl
            }

        # 3. Z-Score и текущая цена (15м)
        resp_15 = client.get_kline(category="linear", symbol=symbol, interval="15", limit=20)
        if resp_15["retCode"] != 0:
            return f"Ошибка данных 15м: {resp_15['retMsg']}"

        prices = [float(x[4]) for x in resp_15["result"]["list"]]
        current_price = prices[0]
        mean = np.mean(prices)
        std = np.std(prices)
        z_score = (current_price - mean) / std if std != 0 else 0

        # Определение основного тренда по недельному пивоту
        main_trend = "Unknown"
        if weekly_pivot_data:
            main_trend = "Bullish (Above Weekly Pivot)" if current_price > weekly_pivot_data["pivot"] else "Bearish (Below Weekly Pivot)"

        return {
            "current_price": current_price,
            "main_trend": main_trend,
            "weekly_pivots": weekly_pivot_data,
            "daily_pivots": daily_pivot_data,
            "z_score": round(z_score, 4)
        }
    except Exception as e:
        return f"Критическая ошибка при расчете индикаторов: {e}"

