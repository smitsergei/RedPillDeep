from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from core.llm import get_llm
from tools.trade_tools import place_order, set_sl_tp, cancel_all_symbol_orders

def create_trader_agent():
    llm = get_llm()
    tools = [place_order, set_sl_tp, cancel_all_symbol_orders]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Ты - исполнительный трейдер.
Твоя задача: ТОЧНО выполнять торговый план, полученный от руководства.

1. Если план содержит команду на открытие - выставляй ордер и СРАЗУ ставь SL и TP.
2. Если план содержит команду на закрытие - закрывай позицию по рынку и отменяй ордера.
3. Возвращай отчет об исполнении (ID ордеров, цены исполнения)."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)
