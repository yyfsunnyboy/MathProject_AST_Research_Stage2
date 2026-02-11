# ==============================================================================
# ID: jh_數學1上_FourArithmeticOperationsOfIntegers
# Model: gemini-2.5-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 48.83s | Tokens: In=548, Out=1840
# Created At: 2026-02-09 17:10:34
# Fix Status: [Basic Cleanup] | Fixes: Basic=1, Advanced=(Regex=0, AST=0)
# Verification: Internal Logic Check = FAILED
# ==============================================================================
import random

def _generate_basic_operand_str(level):
    """
    Generates strings for a basic operand (a number or a simple (num op num) expression).
    Returns (eval_str, display_str).
    """
    if level == 1 or random.random() < 0.7: # Higher chance of just a number for level 1
        num = random.randint(-20, 20)
        eval_str = str(num)
        display_str = str(num) if num >= 0 else f"({num})" # Display negative numbers with parentheses
        return eval_str, display_str
    else:
        op = random.choice(['+', '-', '*'])
        num1 = random.randint(-20, 20)
        num2 = random.randint(-20, 20)
        eval_str = f"({num1}{op}{num2})"
        display_str = f"[({num1}){op}({num2})]" # Use [] for outer parentheses in display
        return eval_str, display_str

def generate(level=1, **kwargs):
    """