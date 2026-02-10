from typing import List, Optional
from pydantic import BaseModel, Field
from langchain.tools import tool
from agents.analyst import create_analyst_agent
from agents.money_manager import create_mm_agent
from agents.trader import create_trader_agent
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from core.llm import get_llm

# Инициализируем субагентов
analyst_executor = create_analyst_agent()
mm_executor = create_mm_agent()
trader_executor = create_trader_agent()

class AnalystInput(BaseModel):
    query: str = Field(description="Инструкция для аналитика по анализу рынка")

class MMInput(BaseModel):
    analysis_result: str = Field(description="Результат анализа от аналитика")
    balance_info: Optional[str] = Field(default=None, description="Дополнительная информация о балансе")

class TraderInput(BaseModel):
    execution_plan: str = Field(description="Финальный план сделки от мани-менеджера")

@tool("market_analyst", args_schema=AnalystInput)
def call_analyst(query: str):
    """Вызывает субагента-аналитика. Он анализирует 15м свечи, Pivot уровни и Z-Score. 
    Возвращает торговую рекомендацию."""
    result = analyst_executor.invoke({"input": query, "chat_history": []})
    return result["output"]

@tool("money_manager", args_schema=MMInput)
def call_money_manager(analysis_result: str, balance_info: str = ""):
    """Вызывает субагента мани-менеджера. Он рассчитывает Qty и риск на основе анализа рынка.
    Принимает результат анализа. Возвращает четкие параметры ордера."""
    input_text = f"Анализ: {analysis_result}. Инфо о балансе: {balance_info}"
    result = mm_executor.invoke({"input": input_text, "chat_history": []})
    return result["output"]

@tool("execution_trader", args_schema=TraderInput)
def call_trader(execution_plan: str):
    """Вызывает субагента-трейдера для исполнения сделки на Bybit.
    Принимает план от мани-менеджера. Возвращает статус исполнения и ID ордеров."""
    result = trader_executor.invoke({"input": execution_plan, "chat_history": []})
    return result["output"]

def create_supervisor_agent():
    llm = get_llm()
    # Список инструментов-субагентов
    tools = [call_analyst, call_money_manager, call_trader]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Ты - Диспетчер (Supervisor) мультиагентной системы RedPill.
Твое распоряжение: команда специализированных субагентов.

ТВОЯ ЛОГИКА РАБОТЫ:
1. Когда поступает задача на торговлю, ты ОБЯЗАН сначала вызвать 'market_analyst'.
2. Получив отчет от аналитика, ты передаешь его 'money_manager' для расчета рисков и объема.
3. Если 'money_manager' подтверждает вход и дает параметры (Qty, SL, TP), ты вызываешь 'execution_trader'.
4. Если аналитик или мани-менеджер говорят 'Hold' или 'Не торговать', ты завершаешь цикл и докладываешь причину.

Ты не выполняешь расчеты сам. Ты делегируешь задачи и собираешь итоговый отчет.
Веди лог действий в рамках одного цикла."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)
