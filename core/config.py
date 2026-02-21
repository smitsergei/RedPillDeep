import os
from dotenv import load_dotenv

# Принудительно загружаем .env из текущей директории
load_dotenv(override=True)

class Config:
    BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
    BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET")
    # По умолчанию False (Mainnet), если не указано иное
    BYBIT_TESTNET = os.getenv("BYBIT_TESTNET", "false").lower() == "true"
    
    # Конфигурация Z.ai
    ZAI_API_KEY = os.getenv("ZAI_API_KEY")
    ZAI_BASE_URL = "https://api.z.ai/api/anthropic"
    MODEL_NAME = "claude-opus-4-6"
    
    SYMBOL = "ETHUSDT"

    # Telegram конфигурация
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    # ID пользователя, команды которого бот будет слушать
    TELEGRAM_ALLOWED_USER_ID = os.getenv("TELEGRAM_ALLOWED_USER_ID")
    # ID чата (личка или группа), куда бот будет слать 15-минутные отчеты
    # Если не указан - шлет в личку (ALLOWED_USER_ID)
    TELEGRAM_REPORT_CHAT_ID = os.getenv("TELEGRAM_REPORT_CHAT_ID", TELEGRAM_ALLOWED_USER_ID)
