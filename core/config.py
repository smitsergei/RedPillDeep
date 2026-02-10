import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
    BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET")
    BYBIT_TESTNET = os.getenv("BYBIT_TESTNET", "true").lower() == "true"
    
    # Конфигурация Z.ai
    ZAI_API_KEY = os.getenv("ZAI_API_KEY")
    ZAI_BASE_URL = "https://api.z.ai/api/anthropic"
    MODEL_NAME = "claude-opus-4-6"

    SYMBOL = "BTCUSDT"
