from langchain.agents import create_agent
from core.llm import get_llm
from tools.trade_tools import place_order, set_sl_tp, cancel_all_symbol_orders, amend_order
from tools.market_tools import get_open_positions, get_instrument_info

def create_trader_agent():
    llm = get_llm()
    # Полный набор инструментов для Трейдера
    tools = [
        place_order, 
        set_sl_tp, 
        cancel_all_symbol_orders, 
        amend_order, 
        get_open_positions,
        get_instrument_info
    ]
    
    system_prompt = """Ты - старший исполнительный трейдер на бирже Bybit (API V5).
Твоя задача: БЕЗУПРЕЧНО реализовать финальный торговый план.

ТВОИ ДЕЙСТВИЯ:
1. ПОЛУЧИ ПАРАМЕТРЫ: Перед выставлением ордера проверь `get_instrument_info` для подтверждения `tickSize` и `qtyStep`.
2. ВЫПОЛНЕНИЕ: 
   - Если это новый вход: Используй `place_order` с `tp` и `sl`.
   - Если нужно изменить текущий лимитный ордер: Используй `amend_order`.
   - Если нужно закрыть позицию: Выставь противоположный рыночный ордер через `place_order`.
3. КОНТРОЛЬ: После любого действия через 1-2 секунды проверь `get_open_positions`, чтобы убедиться, что всё прошло корректно.

ВАЖНО:
- Все числовые параметры передавай как СТРОКИ.
- По умолчанию `position_idx=0` (односторонний режим).
- Если `entry` указан как 'Market', `order_type` должен быть 'Market'.

ОТЧЕТ:
После завершения работы выдай краткий список выполненных действий, ID ордеров и текущий статус позиции."""

    return create_agent(model=llm, tools=tools, system_prompt=system_prompt)
