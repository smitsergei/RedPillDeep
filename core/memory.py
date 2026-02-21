import json
import os
from typing import Dict, Optional

PLAN_FILE = "trading_plan.json"

class TradingPlanManager:
    """Управляет сохранением и чтением торгового плана в JSON файл."""
    
    @staticmethod
    def get_plan() -> Dict:
        if not os.path.exists(PLAN_FILE):
            return {
                "status": "No active plan",
                "last_update": None,
                "direction": None,
                "levels": {},
                "strategy": "Wait for signal"
            }
        try:
            with open(PLAN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"error": "Failed to read plan"}

    @staticmethod
    def update_plan(plan_data: Dict) -> str:
        try:
            with open(PLAN_FILE, "w", encoding="utf-8") as f:
                json.dump(plan_data, f, indent=4, ensure_ascii=False)
            return "Торговый план успешно обновлен."
        except Exception as e:
            return f"Ошибка при обновлении плана: {e}"

trading_plan_manager = TradingPlanManager()
