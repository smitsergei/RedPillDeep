# Flexible Position Management Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:execiting-plans to implement this plan task-by-task.

**Goal:** Разработать и внедрить логику гибкого управления открытыми позициями: усреднение/доливка (Scale In), частичная фиксация (Partial TP/Scale Out), перевод стопа в безубыток (Move to BE) и полное закрытие.

**Architecture:** 
1. Дополнение `Analyst` логикой анализа открытых позиций (Управление vs Поиск входа).
2. Расширение `Money Manager` расчетом рисков для "доливок" и частичных закрытий.
3. Добавление параметра `reduce_only` в инструмент `place_order` для безопасного сокращения позиций.
4. Обновление `Trader` для исполнения команд на изменение стопов и частичного выхода.

**Tech Stack:** Python, LangChain, Bybit API (pybit).

---

### Task 1: Update Trader Tools with `reduce_only`

**Files:**
- Modify: `tools/trade_tools.py`

**Step 1: Add `reduce_only` to `place_order`**

Update `place_order` signature and params to support `reduceOnly`.

```python
@tool
def place_order(
    symbol: str, 
    side: str, 
    order_type: str, 
    qty: str, 
    price: str = None, 
    tp: str = None, 
    sl: str = None,
    tpsl_mode: str = "Full",
    position_idx: int = 0,
    reduce_only: bool = False
):
    """
    Выставляет ордер на бирже.
    side: 'Buy' или 'Sell'
    order_type: 'Market' или 'Limit'
    tp/sl: цены Take Profit и Stop Loss (устанавливаются сразу с ордером)
    tpsl_mode: 'Full' или 'Partial'
    position_idx: 0 (One-Way), 1 (Hedge Buy), 2 (Hedge Sell)
    reduce_only: Если True, ордер может только уменьшить позицию.
    """
    try:
        params = {
            "category": "linear",
            "symbol": symbol,
            "side": side,
            "orderType": order_type,
            "qty": str(qty),
            "positionIdx": position_idx,
            "tpslMode": tpsl_mode,
            "reduceOnly": reduce_only
        }
        # ... (other params)
```

**Step 2: Commit**

```bash
git add tools/trade_tools.py
git commit -m "feat: add reduceOnly support to place_order tool"
```

---

### Task 2: Update Analyst Agent Prompt

**Files:**
- Modify: `agents/analyst.py`

**Step 1: Update system prompt**

Add logic for position management:
- Если есть открытые позиции (проверять через `get_open_positions`), Аналитик должен решить:
  - **HOLD**: Держать без изменений.
  - **ADD (Scale In)**: Увеличить позицию, если тренд подтверждается и есть запас до уровней.
  - **MOVE_TO_BE**: Перенести стоп в безубыток (вход + комиссия), если цена прошла > 1% или дошла до mid-уровня.
  - **PARTIAL_CLOSE**: Закрыть часть (например, 50%) у сильного уровня.
  - **CLOSE**: Закрыть всё.

**Step 2: Commit**

```bash
git add agents/analyst.py
git commit -m "prompt: add flexible position management logic to Analyst"
```

---

### Task 3: Update Money Manager Agent Prompt

**Files:**
- Modify: `agents/money_manager.py`

**Step 1: Update system prompt**

Add rules for Scaling In/Out:
- **Scaling In**: Суммарный риск по символу не должен превышать 2% (или иное заданное значение). Расчет Qty для доливки = (Оставшийся Риск в USDT) / (Новое Расстояние до SL).
- **Scaling Out**: Подтверждать объем для частичного закрытия (Qty_to_close = Qty_current * 0.5).
- **Move to BE**: Подтверждать цену входа как новый SL.

**Step 2: Commit**

```bash
git add agents/money_manager.py
git commit -m "prompt: update Money Manager with scaling and BE calculation rules"
```

---

### Task 4: Update Trader Agent Prompt

**Files:**
- Modify: `agents/trader.py`

**Step 1: Update system prompt**

Add execution rules for management:
- **MOVE_TO_BE**: Использовать `set_sl_tp` для обновления стопа на цену входа.
- **PARTIAL_CLOSE**: Использовать `place_order` с `reduce_only=True` и `order_type='Market'` (или лимитку).
- **ADD**: Обычный `place_order`, но учитывать, что позиция уже есть (аккуратно с `position_idx`).

**Step 2: Commit**

```bash
git add agents/trader.py
git commit -m "prompt: update Trader for partial exits and BE protection"
```

---

### Task 5: End-to-End Verification (Simulation/Dry Run)

**Step 1: Verify Analyst detects position and suggests BE**
- Запустить цикл (в логах или тесте), имитируя открытую прибыльную позицию.
- Убедиться, что Аналитик выдает команду `MOVE_TO_BE`.

**Step 2: Verify Trader executes BE**
- Убедиться, что Трейдер вызывает `set_sl_tp` с корректной ценой.

**Step 3: Commit all remaining changes**

```bash
git add .
git commit -m "feat: complete flexible position management implementation"
```
