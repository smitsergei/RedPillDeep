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

@tool
def analyze_candlestick_patterns(symbol: str = Config.SYMBOL, limit: int = 50):
    """Анализирует 15-минутные свечи: определяет тренд, диапазон консолидации, паттерны Price Action для входа."""
    try:
        resp = client.get_kline(category="linear", symbol=symbol, interval="15", limit=limit)
        if resp["retCode"] != 0:
            return f"Ошибка данных: {resp['retMsg']}"

        candles = resp["result"]["list"]
        # candles: [startTime, open, high, low, close, volume, ...]

        # Парсим данные
        data = []
        for c in candles:
            data.append({
                "open": float(c[1]),
                "high": float(c[2]),
                "low": float(c[3]),
                "close": float(c[4]),
                "volume": float(c[5])
            })

        # Определяем тренд по последним 20 свечам
        recent = data[:20]
        highs = [x["high"] for x in recent]
        lows = [x["low"] for x in recent]
        closes = [x["close"] for x in recent]

        # Уровни диапазона (High/Low за период)
        range_high = max(highs)
        range_low = min(lows)
        current_price = data[0]["close"]
        range_size = range_high - range_low

        # Положение цены в диапазоне (0-100%)
        price_position = ((current_price - range_low) / range_size * 100) if range_size > 0 else 50

        # Определение тренда
        higher_highs = sum(1 for i in range(len(recent)-1) if recent[i]["high"] > recent[i+1]["high"])
        higher_lows = sum(1 for i in range(len(recent)-1) if recent[i]["low"] > recent[i+1]["low"])
        trend = "NEUTRAL"
        if higher_highs > 12 and higher_lows > 12:
            trend = "UPTREND"
        elif higher_highs < 8 and higher_lows < 8:
            trend = "DOWNTREND"
        elif range_size / current_price < 0.01:  # диапазон менее 1%
            trend = "RANGE/CONSOLIDATION"

        # Анализ последней свечи (текущей)
        last = data[0]
        body = abs(last["close"] - last["open"])
        wick_up = last["high"] - max(last["open"], last["close"])
        wick_down = min(last["open"], last["close"]) - last["low"]
        total_range = last["high"] - last["low"]

        # Определение типа свечи
        candle_type = "UNKNOWN"
        if body > total_range * 0.7:
            candle_type = "STRONG_BULLISH" if last["close"] > last["open"] else "STRONG_BEARISH"
        elif body < total_range * 0.3:
            candle_type = "DOJI_INDECISION"
        elif wick_up > body * 2:
            candle_type = "HAMMER_BULLISH" if last["close"] > last["open"] else "SHOOTING_STAR_BEARISH"
        elif wick_down > body * 2:
            candle_type = "INVERTED_HAMMER"

        # Паттерны из 2-3 последних свечей
        patterns = []
        if len(data) >= 2:
            prev = data[1]
            # Бычье поглощение
            if last["close"] > last["open"] and prev["close"] < prev["open"]:
                if last["open"] < prev["close"] and last["close"] > prev["open"]:
                    patterns.append("BULLISH_ENGULFING")
            # Медвежье поглощение
            if last["close"] < last["open"] and prev["close"] > prev["open"]:
                if last["open"] > prev["close"] and last["close"] < prev["open"]:
                    patterns.append("BEARISH_ENGULFING")

        if len(data) >= 3:
            # Утренняя звезда (бычий разворот)
            if (data[2]["close"] < data[2]["open"] and  # медвежья
                data[1]["body"] < total_range * 0.3 and  # доджи
                last["close"] > last["open"]):  # бычья
                patterns.append("MORNING_STAR_BULLISH")

        # Рекомендации по входу на основе.levels
        entry_signals = []
        if trend == "RANGE/CONSOLIDATION":
            if price_position < 20:
                entry_signals.append("NEAR_SUPPORT - возможен LONG от отката")
            elif price_position > 80:
                entry_signals.append("NEAR_RESISTANCE - возможен SHORT от отката")
        elif trend == "UPTREND":
            if price_position < 40:
                entry_signals.append("DIP_IN_UPTREND - возможен LONG на откате")
        elif trend == "DOWNTREND":
            if price_position > 60:
                entry_signals.append("RALLY_IN_DOWNTREND - возможен SHORT на отскоке")

        return {
            "trend": trend,
            "current_price": current_price,
            "range": {"high": range_high, "low": range_low, "size_pct": round(range_size/current_price*100, 3)},
            "price_position_pct": round(price_position, 1),
            "last_candle": {
                "type": candle_type,
                "open": last["open"],
                "high": last["high"],
                "low": last["low"],
                "close": last["close"],
                "volume": last["volume"]
            },
            "patterns": patterns,
            "entry_signals": entry_signals
        }
    except Exception as e:
        return f"Ошибка свечного анализа: {e}"

