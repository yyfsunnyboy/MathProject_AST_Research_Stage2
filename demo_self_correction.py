
import os
import time
import textwrap
import logging
from datetime import datetime
import traceback

# 1. Mock Environment Setup (模擬環境設置)
# 為了讓 script 獨立運行，我們需要 mock 一部分 core 的模組
# 讓它可以直接從 test_self_correction.py 執行，而不需要依賴整個專案的 database
class MockAIClient:
    def __init__(self):
        print("[MockAI] AI Client Initialized")

    def chat_completion(self, messages, model_size='14b'):
        print(f"\n[MockAI] Sending request to {model_size} model...")
        print(f"[MockAI] Prompt Preview (last message): {messages[-1]['content'][:200]}...")
        
        # 這裡會真正呼叫 Ollama (假設環境有安裝 requests)，或者是模擬返回
        # 為了真實演示，我們嘗試呼叫真正的 Ollama 接口
        try:
            import requests
            
            # 使用 qwen2.5-coder:14b
            model_name = "qwen2.5-coder:14b"
            
            payload = {
                "model": model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.2, # 低一點讓它專注修復
                    "num_ctx": 4096
                }
            }
            
            response = requests.post("http://localhost:11434/api/chat", json=payload)
            response.raise_for_status()
            result = response.json()
            content = result['message']['content']
            print("\n[MockAI] Response Received!")
            return content
            
        except Exception as e:
            print(f"[MockAI] Error calling Ollama: {e}")
            return "Error: Could not call AI model."

# 2. The Broken Code (模擬剛剛失敗的代碼)
BROKEN_CODE = r"""
import random
import math

def generate(level=1, **kwargs):
    while True:
        # Step 1: Generate Expr_A's operands and operators
        num_operands_A = random.choice([3, 4])
        operands_A = [random.randint(-20, -1) if random.random() < 0.3 else random.randint(1, 20) for _ in range(num_operands_A)]
        operators_A = [random.choice(['+', '-', '*', '/']) for _ in range(num_operands_A - 1)]

        # Ensure at least one '*' or '/' in Expr_A
        if not any(op in ['*', '/'] for op in operators_A):
            continue

        # Calculate Part A's value
        val = operands_A[0]
        try:
            for i, op in enumerate(operators_A):
                n = operands_A[i + 1]
                if op == '/' and val % n != 0:
                    raise ValueError("Not an integer division")
                val = eval(f"{val} {op} {n}")
                if abs(val) > 500:
                    raise ValueError("Intermediate result out of range")
            # Problem: Missing 'val_A = val' assignment here!
        except Exception as e:
            continue

        # Step 2: Calculate Part B's value
        num_operands_C = random.choice([2, 3])
        operands_C = [random.randint(-100, -1) if random.random() < 0.3 else random.randint(1, 100) for _ in range(num_operands_C)]
        operators_C = [random.choice(['+', '-', '*', '/']) for _ in range(num_operands_C - 1)]
        
        # ... logic for C ...
        val_C = 100 # Mock value for C
        val_B = abs(val_C)

        # Step 4: Calculate final answer
        main_op = random.choice(['+', '-'])
        # ERROR triggers here: val_A is not defined
        final_answer = eval(f"{val_A} {main_op} {val_B}")
        
        return {'question_text': "mock", 'correct_answer': str(final_answer), 'answer': str(final_answer), 'mode': 1}
"""

# 3. Execution & Validation Function (執行與驗證)
def validate_code(code_str):
    try:
        namespace = {}
        # 1. Compile
        compiled = compile(code_str, '<string>', 'exec')
        exec(compiled, namespace)
        
        # 2. Run generate
        if 'generate' not in namespace:
            return False, "Function 'generate' not found."
        
        # 3. Execute
        result = namespace['generate']()
        return True, None
        
    except Exception as e:
        # Get traceback
        error_msg = traceback.format_exc()
        # Extract the last few lines for cleaner prompt
        relevant_trace = error_msg.split('\n')[-4:] 
        return False, f"{e.__class__.__name__}: {str(e)}\n" + "\n".join(relevant_trace)

# 4. Self-Correction Logic (Core Concept)
def run_self_correction_demo():
    print("🚀 [Demo] Starting Self-Correction Experiment")
    ai = MockAIClient()
    
    current_code = BROKEN_CODE
    max_retries = 2
    
    # Round 0: Initial Try (Simulated as already failed)
    print("\n--- Round 0: Initial Validation ---")
    is_valid, error = validate_code(current_code)
    
    if is_valid:
        print("✅ Code passed unexpectedly!")
        return
    else:
        print(f"❌ Verification Failed. Error:\n{error}")

    # Start Feedback Loop
    for attempt in range(1, max_retries + 1):
        print(f"\n--- Round {attempt}: Self-Correction Attempt ---")
        
        # Construct Prompt
        prompt = f"""
You are an expert Python debugger. The following code failed to execute.
Please fix the logic error based on the error message provided.

[BROKEN CODE]:
{current_code}

[ERROR MESSAGE]:
{error}

[INSTRUCTIONS]:
1. Identify the variable or logic causing the crash.
2. Fix the code to ensure it runs correctly and returns valid output.
3. OUTPUT ONLY THE FULL FIXED PYTHON CODE. NO MARKDOWN, NO EXPLANATION.
"""
        messages = [
            {"role": "system", "content": "You are a Python coding assistant. Output only raw code."},
            {"role": "user", "content": prompt}
        ]
        
        # Call AI
        new_code_raw = ai.chat_completion(messages)
        
        # Clean Code (Basic)
        new_code = new_code_raw.replace("```python", "").replace("```", "").strip()
        
        print("\n[Self-Correction] New code received. Validating...")
        
        # Validate Again
        is_valid, error = validate_code(new_code)
        
        if is_valid:
            print(f"✨ SUCCESS! The model fixed the code in attempt {attempt}!")
            print(f"Final Code Snippet (Fix Location):\n")
            # 簡單展示修復的地方
            lines = new_code.split('\n')
            for i, line in enumerate(lines):
                 if "val_A =" in line:
                     print(f"{i+1}: {line}  <-- FIXED HERE!")
            return
        else:
            print(f"❌ Code still failing with error: {error}")
            current_code = new_code # Update code for next round (iterative fixing)

    print("\n💀 Failed to fix code after max retries.")

if __name__ == "__main__":
    run_self_correction_demo()
