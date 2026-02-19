from langchain.tools import tool
from core.bybit_client import get_bybit_client

client = get_bybit_client()

@tool
def get_wallet_balance():
    """Получает текущий баланс аккаунта USDT."""
    try:
        response = client.get_wallet_balance(accountType="UNIFIED", coin="USDT")
        if response["retCode"] == 0:
            return response["result"]["list"][0]["coin"][0]["walletBalance"]
        return f"Ошибка Bybit (retCode {response['retCode']}): {response['retMsg']}"
    except Exception as e:
        return f"Критическая ошибка при получении баланса: {e}"

@tool
def get_account_info():
    """Возвращает настройки аккаунта: режим маржи и текущее плечо (leverage)."""
    try:
        response = client.get_account_info()
        if response["retCode"] == 0:
            return response["result"]
        return f"Ошибка Bybit: {response['retMsg']}"
    except Exception as e:
        return f"Критическая ошибка при получении настроек аккаунта: {e}"

@tool
def get_execution_history(limit: int = 10):
    """Возвращает историю исполненных сделок."""
    try:
        response = client.get_executions(category="linear", limit=limit)
        if response["retCode"] == 0:
            return response["result"]["list"]
        return f"Ошибка Bybit (retCode {response['retCode']}): {response['retMsg']}"
    except Exception as e:
        return f"Критическая ошибка при получении истории: {e}"
