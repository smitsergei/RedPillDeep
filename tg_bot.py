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

import json
import re
import ast

def format_agent_response(response: str) -> str:
    """Форматирует ответ агента, извлекая только текст из структурированных данных."""
    # Пробуем распарсить как Python-список словарей
    if response.strip().startswith('[') and response.strip().endswith(']'):
        try:
            # Пробуем ast.literal_eval (безопаснее eval)
            data = ast.literal_eval(response)
            if isinstance(data, list):
                texts = []
                for item in data:
                    if isinstance(item, dict):
                        # Пропускаем thinking
                        if item.get('type') == 'thinking':
                            continue
                        if 'text' in item:
                            texts.append(item['text'])
                        elif 'content' in item:
                            texts.append(item['content'])
                    elif isinstance(item, str):
                        texts.append(item)
                if texts:
                    return '\n\n'.join(texts)
        except:
            # Если не получилось, пробуем конвертировать одинарные кавычки в двойные для JSON
            try:
                # Заменяем одинарные кавычки на двойные (осторожно, только для ключей)
                json_str = response.replace("'", '"')
                data = json.loads(json_str)
                if isinstance(data, list):
                    texts = []
                    for item in data:
                        if isinstance(item, dict):
                            if item.get('type') == 'thinking':
                                continue
                            if 'text' in item:
                                texts.append(item['text'])
                            elif 'content' in item:
                                texts.append(item['content'])
                        elif isinstance(item, str):
                            texts.append(item)
                    if texts:
                        return '\n\n'.join(texts)
            except:
                pass

    # Если не удалось распарсить как структуру, очищаем regex
    # Удаляем блоки словарей полностью через многострочный regex
    # Удаляем {...} блоки, которые содержат 'signature' или 'thinking'
    cleaned = re.sub(r"\{'signature':[^}]*\}", '', response, flags=re.DOTALL)
    cleaned = re.sub(r"\{\"signature\":[^}]*\}", '', cleaned, flags=re.DOTALL)

    # Удаляем 'thinking': '...' блоки
    cleaned = re.sub(r"'thinking':\s*'[^']*'", '', cleaned)
    cleaned = re.sub(r'"thinking":\s*"[^"]*"', '', cleaned)

    # Удаляем 'type': 'thinking' строки
    cleaned = re.sub(r"'type':\s*'thinking'", '', cleaned)
    cleaned = re.sub(r'"type":\s*"thinking"', '', cleaned)

    # Удаляем оставшиеся ключи без значений
    cleaned = re.sub(r",\s*", '', cleaned)  # лишние запятые
    cleaned = re.sub(r"\[\s*,\s*", '[', cleaned)  # [,  → [
    cleaned = re.sub(r"\s*,\s*\]", ']', cleaned)  # , ] → ]

    # Убираем пустые словари
    cleaned = re.sub(r"\{\}", '', cleaned)
    cleaned = re.sub(r"\{\}", '', cleaned)

    # Очищаем от лишних пробелов и пустых строк
    lines = cleaned.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("']") and not line.startswith('"}'):
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines) if cleaned_lines else response

def convert_markdown_to_html(text: str) -> str:
    """Конвертирует простую Markdown разметку в HTML."""
    # Заменяем **текст** на <b>текст</b> — работаем парами
    result = ""
    i = 0
    while i < len(text):
        if i + 1 < len(text) and text[i:i+2] == "**":
            # Ищем закрывающую **
            j = i + 2
            while j < len(text):
                if j + 1 < len(text) and text[j:j+2] == "**":
                    # Нашли пару — заменяем на HTML теги
                    inner = text[i+2:j]
                    result += f"<b>{inner}</b>"
                    i = j + 2
                    break
                j += 1
            else:
                # Закрывающая не найдена — оставляем как есть
                result += text[i]
                i += 1
        else:
            result += text[i]
            i += 1
    return result

async def send_long_message(chat_id, text, bot_instance):
    """Отправляет длинное сообщение частями, если превышает лимит Telegram."""
    MAX_LENGTH = 4000  # С небольшим запасом от лимита 4096

    # Форматируем перед отправкой
    formatted_text = format_agent_response(text)

    # Конвертируем Markdown в HTML
    formatted_text = convert_markdown_to_html(formatted_text)

    # Если в тексте есть HTML теги — используем HTML, иначе без форматирования
    has_html = '<b>' in formatted_text or '<i>' in formatted_text or '<code>' in formatted_text

    if len(formatted_text) <= MAX_LENGTH:
        await bot_instance.send_message(
            chat_id=chat_id,
            text=formatted_text,
            parse_mode="HTML" if has_html else None
        )
    else:
        # Разбиваем на части, стараясь не резать по строкам
        parts = []
        current_part = ""

        for line in formatted_text.split('\n'):
            if len(current_part) + len(line) + 1 <= MAX_LENGTH:
                current_part += line + '\n'
            else:
                if current_part:
                    parts.append(current_part.rstrip())
                current_part = line + '\n'

        if current_part:
            parts.append(current_part.rstrip())

        # Отправляем части
        for i, part in enumerate(parts, 1):
            prefix = f"\[Часть {i}/{len(parts)}]\n\n" if len(parts) > 1 else ""
            await bot_instance.send_message(
                chat_id=chat_id,
                text=prefix + part,
                parse_mode="HTML" if has_html else None
            )

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

    # Получаем ответ и извлекаем только текст (без thinking блоков)
    last_message = result["messages"][-1]
    response_text = extract_text_from_content(last_message.content)

    # Сохраняем в историю только текст (без thinking)
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
        await send_long_message(message.chat.id, response_text, message.bot)
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
                    await send_long_message(Config.TELEGRAM_REPORT_CHAT_ID, f"🔔 **Отчет по циклу:**\n\n{response_text}", bot)
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
