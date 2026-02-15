import os
import json
import glob
import time
import ast
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# ==========================================
# 1. 設定區域
# ==========================================
GOOGLE_API_KEY = "your_api_key"  # <--- 確認 Key
genai.configure(api_key=GOOGLE_API_KEY)

MODEL_NAME = "gemini-2.5-flash"

response_schema = {
    "type": "OBJECT",
    "properties": {
        "score": {"type": "INTEGER"},
        "severity": {"type": "STRING"},
        "reason": {"type": "STRING"}
    },
    "required": ["score", "severity", "reason"]
}

generation_config = {
    "temperature": 0.1,
    "top_p": 0.95,
    "max_output_tokens": 1024,
    "response_mime_type": "application/json",
    "response_schema": response_schema,
}

safety_settings = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    generation_config=generation_config,
    safety_settings=safety_settings
)

# ==========================================
# 2. Smart AST 分析 (分級制度)
# ==========================================

def analyze_code_robustness(code):
    """
    智慧分級分析：
    Level 3 (Robust): Retry Loop 或 safe_eval
    Level 2 (Moderate): 有 safe_choice 或 Helper Class，但用了 eval
    Level 1 (High Risk): 用了 eval 且無任何 Helper
    """
    try:
        tree = ast.parse(code)
    except Exception as e:
        return "SYNTAX_ERROR", f"Syntax Error: {e}"

    has_retry_loop = False
    safe_calls = []
    unsafe_calls = []
    has_helpers = False # 用來區分 Ab1 和 Ab2
    
    # 1. 偵測 Loop -> Try
    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.While)):
            for child in ast.walk(node):
                if isinstance(child, ast.Try):
                    has_retry_loop = True
                    break
    
    # 2. 偵測函數呼叫與定義
    for node in ast.walk(tree):
        # 檢查是否有 safe_choice 或 Helper Class (Ab2 特徵)
        if isinstance(node, ast.FunctionDef) and node.name == 'safe_choice':
            has_helpers = True
        if isinstance(node, ast.ClassDef) and 'Ops' in node.name: # e.g., IntegerOps
            has_helpers = True

        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            
            if func_name in ['safe_eval', 'check']:
                safe_calls.append(func_name)
            elif func_name in ['eval', 'exec']:
                unsafe_calls.append(func_name)

    # === 判定邏輯 (階梯式評分) ===
    
    # Level 3: Ab3 (Healer)
    if has_retry_loop:
        return "ROBUST", "Detected explicit 'Retry Loop' wrapping critical logic."
    if len(safe_calls) > 0:
        return "ROBUST", f"Detected usage of Safe Functions: {list(set(safe_calls))}."

    # Level 2: Ab2 (Engineered) - 有 eval 但有 Helper
    if 'eval' in unsafe_calls and has_helpers:
        return "MODERATE", "Unsafe 'eval' detected, but code is structured with helpers (safe_choice)."

    # Level 1: Ab1 (Bare) - 有 eval 且無 Helper
    if 'eval' in unsafe_calls:
        return "RISKY", "Unsafe 'eval' detected in raw code without modular helpers."

    return "NEUTRAL", "Standard code structure."

def super_robust_parse(text):
    clean = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(clean)
    except:
        return {"score": 0, "severity": "Unknown", "reason": "Parse Error"}

# ==========================================
# 3. 評測邏輯
# ==========================================

def get_llm_judgment(code_snippet):
    # 1. 執行 Smart AST 分析
    status, evidence = analyze_code_robustness(code_snippet)
    
    # 2. 根據 AST 結果生成強制指令
    if status == "ROBUST":
        # Ab3 -> 10 分
        guidance = f"""
        [SYSTEM VERIFICATION]: 
        - RESULT: PASSED (Robust).
        - EVIDENCE: {evidence}
        - INSTRUCTION: Assign Score 10.
        - SEVERITY: "None".
        - REASONING: "Robustness verified via Healer mechanism."
        """
    elif status == "MODERATE":
        # Ab2 -> 7 分
        guidance = f"""
        [SYSTEM VERIFICATION]: 
        - RESULT: WARNING (Structured but Risky).
        - EVIDENCE: {evidence}
        - INSTRUCTION: Assign Score 7.
        - SEVERITY: "Medium".
        - REASONING: "Code is modular but uses unsafe eval() which risks runtime errors."
        """
    elif status == "RISKY":
        # Ab1 -> 5 分 (這裡就是關鍵差異！)
        guidance = f"""
        [SYSTEM VERIFICATION]: 
        - RESULT: FAILED (High Risk).
        - EVIDENCE: {evidence}
        - INSTRUCTION: Assign Score 5.
        - SEVERITY: "Major".
        - REASONING: "Unsafe eval() usage in unstructured code. High risk of injection or crash."
        """
    else:
        guidance = "[SYSTEM VERIFICATION]: Neutral structure."

    prompt = f"""
    Act as an AI Code Judge. Evaluate the robustness.
    
    Code Snippet:
    ```python
    {code_snippet[:3000]} 
    ```
    
    {guidance}
    
    Generate JSON matching the schema.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return json.dumps({"score": 0, "severity": "API Error", "reason": str(e)})

def run_evaluation():
    base_dir = r"C:\MathProject_AST_Research\codebleu_research\skills"
    files = glob.glob(os.path.join(base_dir, "*_Ab[123]*.py")) # 抓取 Ab1, 2, 3
    
    if not files:
        print(f"❌ 找不到檔案！請確認路徑: {base_dir}")
        return

    print(f"{'File Name':<55} | {'Score':<5} | {'Reason'}")
    print("-" * 120)
    
    for file_path in sorted(files):
        filename = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            code_content = f.read()
            
        raw_response = get_llm_judgment(code_content)
        result = super_robust_parse(raw_response)
        
        score = result.get('score', 0)
        reason = result.get('reason', 'No reason')
        
        display_reason = (reason[:60] + '..') if len(reason) > 60 else reason
        print(f"{filename:<55} | {score:<5} | {display_reason}")
        
        # Debug 顯示判定狀態
        status, _ = analyze_code_robustness(code_content)
        print(f"   [DEBUG] Status: {status}")
        
        time.sleep(1)

if __name__ == "__main__":
    run_evaluation()
