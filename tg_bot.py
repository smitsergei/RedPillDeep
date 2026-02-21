import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from core.config import Config
from agents.supervisor import create_supervisor_agent

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализируем бота и диспетчер
bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Инициализируем агента и историю для Диспетчера
supervisor = create_supervisor_agent()
chat_history = []

async def invoke_supervisor(query: str) -> str:
    """Асинхронная обертка для синхронного вызова LangChain."""
    global chat_history
    
    # Добавляем новое сообщение в историю
    chat_history.append({"role": "user", "content": query})
    
    print(f"\n--- Отправка запроса Диспетчеру ---\n{query}\n----------------------------------")
    
    # Запускаем синхронный .invoke в отдельном потоке (to_thread)
    def _run_sync():
        return supervisor.invoke({"messages": chat_history})
        
    result = await asyncio.to_thread(_run_sync)
    
    # Получаем ответ
    last_message = result["messages"][-1]
    response_text = last_message.content
    
    # Сохраняем ответ в историю
    chat_history.append({"role": "assistant", "content": response_text})
    
    # Ограничиваем размер истории
    if len(chat_history) > 10:
        chat_history = chat_history[-10:]
        
    return response_text

def is_authorized(message: Message) -> bool:
    """Проверка, что пишет авторизованный пользователь."""
    return str(message.from_user.id) == str(Config.TELEGRAM_ALLOWED_USER_ID)

@dp.message(Command("start"))
async def cmd_start(message: Message):
    if not is_authorized(message):
        await message.answer("Доступ запрещен. Ваш ID не совпадает с TELEGRAM_ALLOWED_USER_ID.")
        return
    await message.answer("Привет! Диспетчер RedPill на связи. Напиши мне свой приказ, и я его выполню (например: 'Проанализируй рынок сейчас').")

@dp.message()
async def process_user_message(message: Message):
    """Обработчик всех текстовых сообщений от пользователя."""
    if not is_authorized(message):
        return
        
    query = message.text
    
    # Игнорируем нетекстовые сообщения (картинки, стикеры и т.д.)
    if not query:
        return
        
    # Бот игнорирует сообщения без ключевого слова "red"
    if "red" not in query.lower():
        return
    
    # Посылаем пользователю "печатает...", пока думает агент (это может занять время)
    try:
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    except Exception:
        pass
    
    try:
        response_text = await invoke_supervisor(query)
        await message.answer(response_text)
    except Exception as e:
        error_msg = f"Ошибка выполнения команды: {e}"
        logging.error(error_msg)
        await message.answer(error_msg)

async def trading_cycle():
    """Фоновая задача, которая запускается каждые 15 минут."""
    while True:
        try:
            print("\n--- Начало нового торгового цикла (15 минут) ---")
            query = f"Проведи полный торговый цикл для {Config.SYMBOL}. Начни с проверки текущего торгового плана и его актуальности."
            
            response_text = await invoke_supervisor(query)
            
            print("\nИтог цикла:")
            print(response_text)
            
            # Отправляем сообщение напрямую в чат
            if Config.TELEGRAM_REPORT_CHAT_ID:
                try:
                    await bot.send_message(chat_id=Config.TELEGRAM_REPORT_CHAT_ID, text=f"🔔 **Отчет по циклу:**\n\n{response_text}")
                except Exception as e:
                    logging.error(f"Не удалось отправить сообщение в Telegram: {e}")
            
            print(f"\nОжидание следующего цикла (15 минут)...")
            await asyncio.sleep(15 * 60)
            
        except Exception as e:
            print(f"Ошибка в основном цикле: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(60)

async def start_bot():
    """Запуск фоновой задачи и работы бота (polling)."""
    # Запускаем процесс торговли в фоне
    asyncio.create_task(trading_cycle())
    
    # Запускаем polling для бота
    print("Telegram бот запущен и ожидает сообщений...")
    await dp.start_polling(bot)
