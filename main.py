import asyncio
from tg_bot import start_bot
from core.config import Config

def main():
    print("Запуск мультиагентной системы RedPill с Telegram ботом...")
    
    if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_ALLOWED_USER_ID:
        print("ВНИМАНИЕ: Не заданы TELEGRAM_BOT_TOKEN или TELEGRAM_ALLOWED_USER_ID в .env файле.")
        print("Создайте бота в @BotFather и узнайте свой ID в @userinfobot.")
        
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("\nОстановка системы RedPill...")

if __name__ == "__main__":
    main()
