import time
from agents.supervisor import create_supervisor_agent
from core.config import Config

def main():
    print("Запуск мультиагентной системы RedPill...")
    supervisor = create_supervisor_agent()
    
    chat_history = []
    
    while True:
        try:
            print("
--- Начало нового торгового цикла ---")
            query = "Проведи полный торговый цикл: анализ, расчет рисков и исполнение (если требуется)."
            
            result = supervisor.invoke({"input": query, "chat_history": chat_history})
            print("
Итог цикла:")
            print(result["output"])
            
            # Сохраняем в историю (можно ограничить размер)
            chat_history.append(("human", query))
            chat_history.append(("ai", result["output"]))
            
            if len(chat_history) > 10:
                chat_history = chat_history[-10:]
                
            print("
Ожидание следующего цикла (15 минут)...")
            time.sleep(15 * 60)
            
        except Exception as e:
            print(f"Ошибка в основном цикле: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
