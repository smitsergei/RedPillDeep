from langchain_anthropic import ChatAnthropic
from core.config import Config

def get_llm(temperature=1):
    """
    Настройка Claude для работы в режиме Adaptive Thinking.
    Для этого режима:
    - temperature должна быть 1.0
    - добавляется параметр thinking с бюджетом токенов.
    """
    return ChatAnthropic(
        model=Config.MODEL_NAME,
        temperature=1, # Обязательно 1 для режима thinking
        max_tokens=64000, # Увеличиваем лимит, так как мысли занимают место
        thinking={
            "type": "adaptive", # Используем рекомендованный тип adaptive
            "budget_tokens": 16000 # Бюджет на внутренние рассуждения
        },
        anthropic_api_key=Config.ZAI_API_KEY,
        anthropic_api_url=Config.ZAI_BASE_URL
    )
