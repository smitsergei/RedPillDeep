from langchain.tools import tool
from core.memory import trading_plan_manager
import datetime

@tool
def get_current_trading_plan():
    """Возвращает текущий активный торговый план из памяти."""
    return trading_plan_manager.get_plan()

@tool
def update_trading_plan(plan_description: str, direction: str, target_price: str, stop_loss: str):
    """
    Обновляет или создает новый торговый план в памяти.
    plan_description: Подробное описание логики.
    direction: 'Buy', 'Sell' или 'Hold'.
    target_price: Целевая цена выхода.
    stop_loss: Цена ограничения убытков.
    """
    new_plan = {
        "status": "Active",
        "last_update": str(datetime.datetime.now()),
        "description": plan_description,
        "direction": direction,
        "levels": {
            "entry": "See description",
            "tp": target_price,
            "sl": stop_loss
        }
    }
    return trading_plan_manager.update_plan(new_plan)
