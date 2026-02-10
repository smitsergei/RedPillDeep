from langchain.tools import tool
from core.bybit_client import get_bybit_client

client = get_bybit_client()

@tool
def get_wallet_balance():
    """Получает текущий баланс аккаунта USDT."""
    response = client.get_wallet_balance(accountType="UNIFIED", coin="USDT")
    if response["retCode"] == 0:
        return response["result"]["list"][0]["coin"][0]["walletBalance"]
    return f"Ошибка получения баланса: {response['retMsg']}"

@tool
def get_execution_history(limit: int = 10):
    """Возвращает историю исполненных сделок."""
    response = client.get_executions(category="linear", limit=limit)
    if response["retCode"] == 0:
        return response["result"]["list"]
    return f"Ошибка получения истории: {response['retMsg']}"
