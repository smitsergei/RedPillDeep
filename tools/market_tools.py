import pandas as pd
import numpy as np
from langchain.tools import tool
from core.bybit_client import get_bybit_client
from core.config import Config

client = get_bybit_client()

@tool
def get_klines(symbol: str = Config.SYMBOL, interval: str = "15", limit: int = 5):
    """Получает последние свечи для анализа краткосрочной динамики."""
    response = client.get_kline(
        category="linear",
        symbol=symbol,
        interval=interval,
        limit=limit
    )
    if response["retCode"] == 0:
        return response["result"]["list"]
    return f"Ошибка получения свечей: {response['retMsg']}"

@tool
def get_ticker_price(symbol: str = Config.SYMBOL):
    """Получает текущую цену инструмента."""
    response = client.get_tickers(category="linear", symbol=symbol)
    if response["retCode"] == 0:
        return response["result"]["list"][0]["lastPrice"]
    return f"Ошибка получения цены: {response['retMsg']}"

@tool
def get_open_positions():
    """Возвращает список текущих открытых позиций."""
    response = client.get_positions(category="linear", settleCoin="USDT")
    if response["retCode"] == 0:
        # Фильтруем только активные позиции
        active = [p for p in response["result"]["list"] if float(p["size"]) > 0]
        return active
    return f"Ошибка получения позиций: {response['retMsg']}"

@tool
def calculate_pivot_zscore(symbol: str = Config.SYMBOL):
    """Рассчитывает уровни Pivot и Z-Score на основе данных за последние 24 часа."""
    # Для Pivot нужны данные вчерашнего дня (D)
    resp_d = client.get_kline(category="linear", symbol=symbol, interval="D", limit=2)
    
    if resp_d["retCode"] != 0 or len(resp_d["result"]["list"]) < 2:
        return "Недостаточно данных для расчета"

    # Данные за вчера: [High, Low, Close]
    # В Bybit list возвращает [startTime, open, high, low, close, volume, turnover]
    yesterday = resp_d["result"]["list"][1]
    h, l, c = float(yesterday[2]), float(yesterday[3]), float(yesterday[4])
    
    pivot = (h + l + c) / 3
    r1 = (2 * pivot) - l
    s1 = (2 * pivot) - h

    # Z-Score на основе 15м свечей за последние 20 периодов
    resp_15 = client.get_kline(category="linear", symbol=symbol, interval="15", limit=20)
    prices = [float(x[4]) for x in resp_15["result"]["list"]]
    
    mean = np.mean(prices)
    std = np.std(prices)
    current_price = prices[0]
    z_score = (current_price - mean) / std if std != 0 else 0

    return {
        "pivot": round(pivot, 2),
        "r1": round(r1, 2),
        "s1": round(s1, 2),
        "z_score": round(z_score, 4)
    }
