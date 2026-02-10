from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from core.llm import get_llm
from tools.market_tools import get_klines, get_ticker_price, calculate_pivot_zscore, get_open_positions

def create_analyst_agent():
    llm = get_llm()
    tools = [get_klines, get_ticker_price, calculate_pivot_zscore, get_open_positions]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Ты - высококвалифицированный финансовый аналитик с доступом к инструментам адаптивного мышления.
Твоя задача: провести глубокий анализ рынка BTC/USDT.

Перед тем как выдать итоговый план, ТЫ ДОЛЖЕН:
1. Тщательно проанализировать последние 5 свечей (15м), учитывая объемы и тени свечей.
2. Сопоставить текущую цену с Pivot уровнями (S1, R1, Pivot).
3. Оценить Z-Score: насколько текущее отклонение цены является критическим.
4. Взвесить риски текущего режима (Ведение сделки vs Поиск новой).

Твой итоговый ответ должен быть структурированным и содержать обоснованный ТОРГОВЫЙ ПЛАН:
- Направление (Buy/Sell/Hold)
- Цена входа (или 'Market')
- Stop Loss (обязательно)
- Take Profit (обязательно)
- Краткое обоснование решения."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)
