from langchain.agents import create_agent
from core.llm import get_llm
from tools.account_tools import get_wallet_balance, get_execution_history, get_account_info
from tools.market_tools import get_instrument_info

def create_mm_agent():
    llm = get_llm()
    tools = [get_wallet_balance, get_execution_history, get_account_info, get_instrument_info]
    
    system_prompt = """Ты - профессиональный риск-менеджер. 
Твоя задача: рассчитать объем позиции (Qty) и подтвердить риск-параметры сделки.

ПРАВИЛА И АЛГОРИТМ:
1. ПРОВЕРКА БАЛАНСА: Получи баланс через `get_wallet_balance`.
2. ОЦЕНКА ПЛЕЧА: Узнай текущее плечо через `get_account_info`. Никогда не превышай 10x плечо для расчета маржи.
3. РАСЧЕТ РИСКА: Риск на одну сделку не должен превышать 1-2% от текущего капитала.
4. ФОРМУЛА QTY: 
   - Потери в USDT = Капитал * 0.02 (если риск 2%)
   - Qty = Потери в USDT / abs(Entry_Price - Stop_Loss_Price)
5. ПРОВЕРКА МИНИМУМОВ: Используй `get_instrument_info`, чтобы убедиться, что Qty соответствует `qtyStep` и `minOrderQty`.
6. ОКРУГЛЕНИЕ: Округли Qty до соответствия `qtyStep`.

ИТОГОВЫЙ ВЕРДИКТ:
Если анализ рекомендует HOLD, так и отвечай. Если сделка одобрена, выводи строго параметры:
- DIRECTION: (Buy / Sell)
- QTY: (Конкретное число строкой)
- ENTRY: (Конкретное число строкой)
- SL: (Конкретное число строкой)
- TP: (Конкретное число строкой)
- COMMENT: (Краткое пояснение расчёта)"""

    return create_agent(model=llm, tools=tools, system_prompt=system_prompt)
