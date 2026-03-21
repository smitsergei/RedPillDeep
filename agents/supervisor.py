from typing import List, Optional
from pydantic import BaseModel, Field
from langchain.tools import tool
from agents.analyst import create_analyst_agent
from agents.money_manager import create_mm_agent
from agents.trader import create_trader_agent
from langchain.agents import create_agent
from core.llm import get_llm
from core.config import Config
from tools.memory_tools import get_current_trading_plan
import requests

# Инициализируем субагентов
analyst_executor = create_analyst_agent()
mm_executor = create_mm_agent()
trader_executor = create_trader_agent()

def extract_text_from_content(content) -> str:
    """Извлекает только текст из content, игнорируя thinking блоки."""
    if isinstance(content, str):
        return content

    # Если content — список блоков (режим thinking)
    if isinstance(content, list):
        texts = []
        for block in content:
            # Пропускаем thinking блоки
            if isinstance(block, dict):
                if block.get('type') == 'thinking':
                    continue
                if 'text' in block:
                    texts.append(block['text'])
            elif hasattr(block, 'type'):
                if block.type == 'thinking':
                    continue
                if hasattr(block, 'text'):
                    texts.append(block.text)
                elif hasattr(block, 'content'):
                    texts.append(block.content)
            elif isinstance(block, str):
                texts.append(block)
        return '\n\n'.join(texts) if texts else str(content)

    return str(content)

def send_to_telegram(message_text: str):
    """Синхронная отправка сообщения в Telegram (так как LangChain агенты синхронные)."""
    if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_REPORT_CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": Config.TELEGRAM_REPORT_CHAT_ID,
        "text": message_text
    }

    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Ошибка отправки сообщения субагента в Telegram: {e}")

class AnalystInput(BaseModel):
    query: str = Field(description="Инструкция для аналитика по анализу рынка")

class MMInput(BaseModel):
    analysis_result: str = Field(description="Результат анализа от аналитика")
    balance_info: Optional[str] = Field(default=None, description="Дополнительная информация о балансе")

class TraderInput(BaseModel):
    execution_plan: str = Field(description="Финальный план сделки от мани-менеджера")

@tool("market_analyst", args_schema=AnalystInput)
def call_analyst(query: str):
    """Вызывает субагента-аналитика. Он анализирует рынок, проверяет старый торговый план
    и обновляет его. Возвращает актуальную торговую рекомендацию."""
    result = analyst_executor.invoke({"messages": [{"role": "user", "content": query}]})
    raw_content = result["messages"][-1].content
    response = extract_text_from_content(raw_content)
    print("\n[Аналитик] сформировал отчет.")
    print(f"Отчет:\n{response}\n")
    send_to_telegram(f"📉 **[Аналитик] сформировал отчет:**\n\n{response}")
    return response

@tool("money_manager", args_schema=MMInput)
def call_money_manager(analysis_result: str, balance_info: str = ""):
    """Вызывает субагента мани-менеджера. Он рассчитывает параметры сделки,
    строго следуя торговому плану и лимитам риска."""
    input_text = f"Анализ: {analysis_result}. Инфо о балансе: {balance_info}"
    result = mm_executor.invoke({"messages": [{"role": "user", "content": input_text}]})
    raw_content = result["messages"][-1].content
    response = extract_text_from_content(raw_content)
    print("\n[Мани-менеджер] рассчитал параметры сделки.")
    print(f"Вердикт:\n{response}\n")
    send_to_telegram(f"🧮 **[Мани-менеджер] рассчитал параметры:**\n\n{response}")
    return response

@tool("execution_trader", args_schema=TraderInput)
def call_trader(execution_plan: str):
    """Вызывает субагента-трейдера для исполнения действий, зафиксированных в торговом плане."""
    result = trader_executor.invoke({"messages": [{"role": "user", "content": execution_plan}]})
    raw_content = result["messages"][-1].content
    response = extract_text_from_content(raw_content)
    print("\n[Трейдер] завершил выполнение.")
    print(f"Статус:\n{response}\n")
    send_to_telegram(f"⚡ **[Трейдер] исполнил план:**\n\n{response}")
    return response

def create_supervisor_agent():
    llm = get_llm()
    # Список инструментов-субагентов
    tools = [call_analyst, call_money_manager, call_trader, get_current_trading_plan]
    
    system_prompt = """Ты - Диспетчер (Supervisor) мультиагентной системы RedPill.
Твоя задача: обеспечить преемственность торговой стратегии через ТОРГОВЫЙ ПЛАН.

ТВОЯ ЛОГИКА РАБОТЫ:
1. В начале цикла используй `get_current_trading_plan`, чтобы понять текущую ситуацию.
2. Дай команду 'market_analyst' проанализировать рынок с учетом этого плана.
3. Если аналитик обновил план, передай новый контекст 'money_manager'.
4. Следи, чтобы 'execution_trader' выполнял только те действия, которые одобрены в плане.
5. Если план говорит 'Hold', а агенты хотят торговать (или наоборот), ТЫ должен пресечь ошибку и потребовать обоснования.

Ты хранишь состояние системы в памяти (Trading Plan) и координируешь субагентов для его реализации или коррекции."""

    return create_agent(model=llm, tools=tools, system_prompt=system_prompt)
