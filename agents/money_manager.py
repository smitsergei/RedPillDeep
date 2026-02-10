from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from core.llm import get_llm
from tools.account_tools import get_wallet_balance, get_execution_history

def create_mm_agent():
    llm = get_llm()
    tools = [get_wallet_balance, get_execution_history]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Ты - профессиональный риск-менеджер.
Твоя задача: на основе баланса счета и рекомендаций Аналитика рассчитать параметры сделки.

Правила:
1. Никогда не рискуй более чем 2% от депозита на одну сделку.
2. Рассчитывай Qty (объем) исходя из текущего баланса USDT.
3. Если Аналитик рекомендует закрыть сделку - подтверждай это решение.
4. Выдавай итоговый вердикт: Direction, Qty, Entry Price, SL, TP.

Учитывай историю сделок, чтобы понимать текущую просадку или прибыль."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)
