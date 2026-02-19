import os

def verify_files():
    print("Verifying implementation of flexible position management...")
    
    # Check analyst.py
    with open("agents/analyst.py", "r", encoding="utf-8") as f:
        content = f.read()
        has_be = "MOVE_TO_BE" in content
        has_partial = "PARTIAL_CLOSE" in content
        print(f"Analyst implementation of BE and Partial: {has_be and has_partial}")

    # Check money_manager.py
    with open("agents/money_manager.py", "r", encoding="utf-8") as f:
        content = f.read()
        has_qty_add = "Qty_Add" in content
        has_action = "ACTION" in content
        print(f"MM implementation of Scale In and ACTION list: {has_qty_add and has_action}")

    # Check trader.py
    with open("agents/trader.py", "r", encoding="utf-8") as f:
        content = f.read()
        has_reduce_only = "reduce_only" in content
        print(f"Trader implementation of reduceOnly: {has_reduce_only}")

    # Check trade_tools.py
    with open("tools/trade_tools.py", "r", encoding="utf-8") as f:
        content = f.read()
        has_tool_reduce_only = "reduce_only: bool = False" in content
        print(f"Trade tool support for reduce_only: {has_tool_reduce_only}")

if __name__ == "__main__":
    verify_files()
