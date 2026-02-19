import time
from agents.supervisor import create_supervisor_agent
from core.config import Config

def main():
    print("Запуск мультиагентной системы RedPill...")
    supervisor = create_supervisor_agent()
    
    # В новой версии LangChain 1.x (через create_agent) история хранится как список сообщений
    chat_history = []
    
    while True:
        try:
            print("\n--- Начало нового торгового цикла ---")
            query = f"Проведи полный торговый цикл для {Config.SYMBOL}: анализ, расчет рисков и исполнение (если требуется)."
            
            # Добавляем новое сообщение в историю
            chat_history.append({"role": "user", "content": query})
            
            # Вызываем супервизора
            # create_agent возвращает CompiledStateGraph, который ожидает {'messages': [...]}
            result = supervisor.invoke({"messages": chat_history})
            
            # Получаем ответ (последнее сообщение от AI)
            last_message = result["messages"][-1]
            response_text = last_message.content
            
            print("\nИтог цикла:")
            print(response_text)
            
            # Сохраняем ответ AI в историю
            chat_history.append({"role": "assistant", "content": response_text})
            
            # Ограничиваем размер истории (например, последние 10 сообщений)
            if len(chat_history) > 10:
                chat_history = chat_history[-10:]
                
            print(f"\nОжидание следующего цикла (15 минут)...")
            time.sleep(15 * 60)
            
        except Exception as e:
            print(f"Ошибка в основном цикле: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(60)

if __name__ == "__main__":
    main()
