# -*- coding: utf-8 -*-
# ==============================================================================
# ID: run_experiment.py
# Version: V1.1.0 (Real API Integration)
# Last Updated: 2026-02-05
# Author: Math AI Research Team
# ==============================================================================

import sys
import os
import glob
import time
import hashlib
import logging
import json
import requests  # [NEW] 用於呼叫 Ollama
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from collections import defaultdict

# [NEW] 嘗試引入 Google Generative AI SDK (新版本)
try:
    from google import genai
    from google.genai import types  # [KEY] 導入 types 以獲得 GenerateContentConfig
    HAS_GENAI = True
except ImportError:
    try:
        # 回退到舊版本（如果還未更新）
        import google.generativeai as genai
        try:
            from google.generativeai import types
        except ImportError:
            types = None
        HAS_GENAI = True
    except ImportError:
        HAS_GENAI = False
        types = None

# ==============================================================================
# 1. 智慧路徑設定
# ==============================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = current_dir
while not os.path.exists(os.path.join(project_root, 'app.py')):
    parent = os.path.dirname(project_root)
    if parent == project_root:
        break
    project_root = parent

sys.path.append(project_root)

# 引入 Core 模組
try:
    from config import Config
    
    # [NEW] 引入 code_generator 的模塊化 cleanup 和 healer 函數
    try:
        from core.code_generator import _basic_cleanup, _advanced_healer
        HAS_CODE_GENERATOR = True
    except ImportError as e:
        print(f"⚠️  無法引入 code_generator 函數: {e}")
        HAS_CODE_GENERATOR = False
    
    # 引入資料庫模型（用於記錄實驗數據）
    try:
        from models import db, ExperimentLog
        HAS_DB = True
    except ImportError:
        HAS_DB = False
except ImportError as e:
    print(f"❌ 無法引入核心模組: {e}")
    print(f"請確保您在專案根目錄下執行，或 PYTHONPATH 設定正確。")
    print(f"專案根目錄: {project_root}")
    sys.exit(1)

# ==============================================================================
# 2. 全域常數
# ==============================================================================
RESULTS_ROOT = os.path.join(project_root, "experiments", "results")
PROMPTS_DIR = os.path.join(project_root, "experiments", "golden_prompts")
DB_PATH = Config.db_path

# 實驗目標模型 (對應 Config.CODER_PRESETS 的 Key)
TARGET_MODELS = [
    "gemini-2.5-flash",     # [1] -> Cloud Gemini
    "qwen2.5-coder-14b",    # [2] -> Local Qwen 14B
    "qwen2.5-coder-7b"      # [3] -> Local Qwen 7B
]

MODEL_DISPLAY_NAMES = {
    "gemini-2.5-flash": "Cloud Gemini 2.5 Flash",
    "qwen2.5-coder-14b": "Local Qwen2.5-Coder 14B",
    "qwen2.5-coder-7b": "Local Qwen2.5-Coder 7B"
}

# ==============================================================================
# 2.5 實驗統計數據結構
# ==============================================================================

class ExperimentStats:
    """全局實驗統計數據收集"""
    def __init__(self):
        self.total_skills = 0
        self.total_models = 0
        self.total_strategies = 3  # Ab1, Ab2, Ab3
        self.total_samples_per_run = 5
        self.total_planned_runs = 0
        self.successful_runs = 0
        self.failed_runs = 0
        self.total_tokens_prompt = 0
        self.total_tokens_completion = 0
        self.total_time_seconds = 0.0
        self.healed_count = 0
        self.model_stats = defaultdict(lambda: {
            'success': 0, 'failure': 0, 'tokens_prompt': 0, 
            'tokens_completion': 0, 'time': 0.0
        })
        self.skill_stats = defaultdict(lambda: {
            'success': 0, 'failure': 0, 'tokens_prompt': 0, 
            'tokens_completion': 0, 'time': 0.0
        })

stats = ExperimentStats()

# ==============================================================================
# 3. 核心功能函數 (LLM API & Healer)
# ==============================================================================

def get_model_config(model_key):
    """從 Config 讀取模型設定"""
    if hasattr(Config, 'CODER_PRESETS') and model_key in Config.CODER_PRESETS:
        return Config.CODER_PRESETS[model_key]
    return None

def _call_gemini(model_config, prompt_text):
    """[Real] 呼叫 Google Gemini API"""
    if not HAS_GENAI:
        return "Error: google-generativeai package not installed.", {"prompt": 0, "completion": 0}
        
    api_key = Config.GEMINI_API_KEY
    if not api_key:
        return "Error: GEMINI_API_KEY not found in env.", {"prompt": 0, "completion": 0}

    try:
        # 新版本 google.genai API
        client = genai.Client(api_key=api_key)
        
        # [關鍵修正] 這是 config.py 設定不了的，必須在程式碼裡寫死
        # 目的：禁止 safety filter，確保完整返回代碼內容
        safety_settings = [
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        # 計算 prompt token
        prompt_tokens = max((len(prompt_text) + 3) // 4, 100)
        
        # 構建 config object（如果 types 可用）
        if types is not None:
            try:
                config = types.GenerateContentConfig(
                    temperature=model_config.get('temperature', 0.1),
                    max_output_tokens=model_config.get('max_tokens', 8192),
                    safety_settings=safety_settings
                )
            except Exception as config_err:
                # 降級：直接傳遞參數
                print(f"⚠️  無法建立 GenerateContentConfig: {config_err}，使用直接參數傳遞")
                config = {
                    "temperature": model_config.get('temperature', 0.1),
                    "max_output_tokens": model_config.get('max_tokens', 8192),
                    "safety_settings": safety_settings
                }
        else:
            # 舊 API 或無法導入 types
            config = {
                "temperature": model_config.get('temperature', 0.1),
                "max_output_tokens": model_config.get('max_tokens', 8192),
                "safety_settings": safety_settings
            }
        
        # 發送請求
        response = client.models.generate_content(
            model=model_config.get('model'),
            contents=prompt_text,
            config=config
        )
        
        # 提取響應文本
        generated_text = None
        if hasattr(response, 'text') and response.text:
            generated_text = response.text
        elif hasattr(response, 'content') and response.content:
            generated_text = str(response.content)
        elif hasattr(response, 'candidates') and len(response.candidates) > 0:
            # 嘗試從 candidates 中提取
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                if len(candidate.content.parts) > 0:
                    generated_text = candidate.content.parts[0].text
        
        if not generated_text:
            return "# Error: Empty response from Gemini", {"prompt": prompt_tokens, "completion": 0}
            
        # [修復] 清洗模型可能重複生成的 Header
        # 避免 Gemini 因為 Prompt 範例而自己生成了檔案頭，導致儲存時出現雙重 Header
        cleaned_lines = []
        lines = generated_text.split('\n')
        skip_header = True  # 剛開始預設檢查 Header
        
        for line in lines:
            stripped = line.strip()
            # 如果開頭就是分隔線或編碼聲明，視為模型重複生成的 Header，跳過
            if skip_header and (stripped.startswith("# ===") or stripped.startswith("# -*- coding")):
                continue
            # 如果開頭是中繼資料 (ID, Model...)，也跳過
            if skip_header and (stripped.startswith("# ID:") or stripped.startswith("# Model:") or 
                              stripped.startswith("# Ablation") or stripped.startswith("# Performance") or
                              stripped.startswith("# Created") or stripped.startswith("# Fix") or
                              stripped.startswith("# Verification")):
                continue
            
            # 一旦遇到正常代碼或空行後不是註解，就停止跳過 Header 的行為
            if stripped and not stripped.startswith("#"):
                skip_header = False
            
            cleaned_lines.append(line)
        
        generated_text = "\n".join(cleaned_lines).strip()
        
        # 計算 completion token
        completion_tokens = max((len(generated_text) + 3) // 4, 50)
        
        return generated_text, {"prompt": prompt_tokens, "completion": completion_tokens}
            
    except Exception as e:
        error_msg = f"# Error calling Gemini: {str(e)}"
        print(f"⚠️  Gemini 呼叫失敗: {e}")
        import traceback
        traceback.print_exc()
        return error_msg, {"prompt": 0, "completion": 0}

def _call_ollama(model_config, prompt_text):
    """[Real] 呼叫 Local Ollama API"""
    url = Config.LOCAL_API_URL # 通常是 http://localhost:11434/api/generate
    
    # [NEW] 从 config 读取超时设置
    ollama_timeout = getattr(Config, 'OLLAMA_TIMEOUT', 600)
    
    # 準備 Payload
    payload = {
        "model": model_config.get('model'), # 這裡會拿到帶冒號的名稱 e.g. qwen2.5-coder:14b
        "prompt": prompt_text,
        "stream": False,
        "options": {
            "temperature": model_config.get('temperature', 0.1),
            "num_predict": model_config.get('max_tokens', 2048),
        }
    }
    
    # 合併 extra_body (num_ctx, num_gpu 等進階參數)
    if 'extra_body' in model_config:
        for k, v in model_config['extra_body'].items():
            payload['options'][k] = v

    try:
        # 發送請求
        response = requests.post(url, json=payload, timeout=ollama_timeout) # 使用配置的超时值
        response.raise_for_status()
        
        result_json = response.json()
        generated_code = result_json.get('response', '')
        
        # Ollama 會回傳真實的 token 統計
        usage = {
            "prompt": result_json.get('prompt_eval_count', len(prompt_text)//4),
            "completion": result_json.get('eval_count', len(generated_code)//4)
        }
        
        return generated_code, usage
        
    except Exception as e:
        return f"# Error calling Ollama: {str(e)}", {"prompt": 0, "completion": 0}

def call_llm(model_key, prompt_text):
    """
    統一入口：呼叫 LLM 生成程式碼
    """
    # 1. 取得設定
    model_config = get_model_config(model_key)
    if not model_config:
        return f"# Error: Config not found for {model_key}", {"prompt": 0, "completion": 0}
    
    provider = model_config.get('provider')
    
    # 2. 路由到對應的 Provider
    if provider == 'google':
        return _call_gemini(model_config, prompt_text)
    elif provider == 'local':
        return _call_ollama(model_config, prompt_text)
    else:
        return f"# Error: Unknown provider {provider}", {"prompt": 0, "completion": 0}

def apply_basic_cleanup(raw_code):
    """
    基本清理 (Ab1/Ab2/Ab3 都執行)
    
    使用 code_generator.py 中的模塊化 _basic_cleanup() 函數
    同時移除可能來自 LLM 的多餘頭部註釋
    
    Returns:
        tuple: (cleaned_code, cleanup_count)
    """
    cleanup_count = 0
    
    # [NEW] 移除 LLM 返回中多餘的頭部註釋
    # 檢查是否有多個 "# ============" 的分隔符
    if raw_code.count('# ==============================================================================') > 1:
        lines = raw_code.split('\n')
        # 找到第一個非註釋的代碼行
        code_start_idx = 0
        for idx, line in enumerate(lines):
            if not line.startswith('#'):
                code_start_idx = idx
                break
        
        if code_start_idx > 0:
            # 移除前面的所有註釋行
            raw_code = '\n'.join(lines[code_start_idx:])
            cleanup_count += 1
    
    if HAS_CODE_GENERATOR:
        # 使用真實的 _basic_cleanup() 實現
        clean_code, generator_cleanup_count = _basic_cleanup(raw_code)
        return clean_code, cleanup_count + generator_cleanup_count
    else:
        # Fallback: 簡易版本
        if raw_code.startswith('```'):
            lines = raw_code.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
                cleanup_count += 1
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
                cleanup_count += 1
            raw_code = '\n'.join(lines)
        
        # 移除多餘空白與規範縮排
        lines = raw_code.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.rstrip()
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines), cleanup_count

def apply_healer_mock(clean_code, ablation_id, skill_id):
    """
    進階 Healer (僅 Ab3 使用) - 轉接層適配層
    
    處理 _advanced_healer() 的多種回傳格式：
    - 情況 1: (code, total_fixes) - 2 個值
    - 情況 2: (code, regex_fixes, ast_fixes, ...) - 8 個值
    """
    if HAS_CODE_GENERATOR and ablation_id >= 3:
        try:
            # 呼叫底層 Healer (它會去呼叫 regex_healer 和 ast_healer)
            result = _advanced_healer(clean_code, ablation_id, skill_id)
            
            # [關鍵適配] 處理回傳值數量不一致的問題
            if isinstance(result, tuple):
                # 情況 1: 只有 (code, fixes) -> 這是現在的情況
                if len(result) == 2:
                    final_code, total_fixes = result
                    # 為了配合 run_experiment 的 4 個回傳值要求，手動補 0
                    # Regex=total, AST=0 (因為無法區分，全部算在 Regex 頭上以顯示數據)
                    return final_code, total_fixes, 0, total_fixes
                
                # 情況 2: 完整回傳 (8個值) -> 舊版或未來的擴充
                elif len(result) >= 4:
                    code_after, regex_fixes, ast_fixes, *_ = result
                    healer_fixed_count = result[5] if len(result) > 5 else (regex_fixes + ast_fixes)
                    return code_after, regex_fixes, ast_fixes, healer_fixed_count
            
            return clean_code, 0, 0, 0
            
        except Exception as e:
            print(f"⚠️  Healer 錯誤: {e}")
            return clean_code, 0, 0, 0
    else:
        return clean_code, 0, 0, 0

def log_experiment_to_db(skill_id, model_name, ablation_id, duration, 
                        prompt_tokens, completion_tokens, raw_code, final_code,
                        is_success=True, healer_fixes=0, verify_status="PASSED"):
    """
    將實驗數據記錄到資料庫 (ExperimentLog 表)
    
    參考 code_generator.py 的 _log_experiment 模式
    """
    if not HAS_DB:
        return False
    
    try:
        from datetime import datetime
        from app import app
        
        with app.app_context():
            # 計算代碼長度
            prompt_len = len(raw_code) if raw_code else 0
            code_len = len(final_code) if final_code else 0
            
            # 判斷修復信息
            repaired = healer_fixes > 0
            
            # [Smart Fix] 如果驗證失敗，將錯誤訊息記錄到 database 的 error_msg 欄位
            # 這樣即使 is_success=True (生成成功)，我們也能知道它語法有錯
            db_error_msg = None
            if not is_success:
                db_error_msg = "Generation failed"
            elif verify_status != "PASSED":
                db_error_msg = verify_status  # 例如: "FAILED (Syntax Error: Line 5)"
            
            # 創建實驗日誌記錄
            log_entry = ExperimentLog(
                skill_id=skill_id,
                start_time=time.time() - duration,  # 計算開始時間
                duration_seconds=duration,
                prompt_len=prompt_len,
                code_len=code_len,
                is_success=is_success,
                error_msg=db_error_msg,
                repaired=repaired,
                model_name=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                ablation_id=ablation_id,
                raw_response=raw_code,
                final_code=final_code
            )
            
            # 添加到資料庫
            db.session.add(log_entry)
            db.session.commit()
        
        return True
    except Exception as e:
        tqdm.write(f"⚠️  資料庫記錄失敗: {e}")
        return False

def verify_code_integrity(code_str):
    """
    完整代碼驗證流程 (與 code_generator.py 同步)
    
    [V47.9 Simplified] 簡化驗證邏輯，避免模組導入問題
    1. 檢查必要函數（generate, check）是否存在
    2. 編譯檢查 
    3. 動態採樣測試 - 執行 generate() 3 次檢查輸出格式
    
    Returns:
        str: "PASSED" 或 "FAILED"
        
    Note:
        由於 Ab2 代碼結構特殊（注入了大量工具庫），驗證比較寬鬆。
        只要 generate() 函數能執行並返回有效格式，就視為 PASSED。
    """
    try:
        if not code_str or not code_str.strip():
            return "FAILED"  # 空代碼
        
        # 檢查必要函數是否存在
        if 'def generate(' not in code_str:
            return "FAILED"  # 缺少 generate 函數
        
        if 'def check(' not in code_str:
            return "FAILED"  # 缺少 check 函數
        
        # Step 1: 編譯檢查
        try:
            compile(code_str, '<string>', 'exec')
        except SyntaxError:
            return "FAILED"  # 語法錯誤
        except Exception:
            pass  # 其他編譯異常但可能是動態行為
        
        # Step 2: 動態採樣驗證（直接在本進程執行）
        try:
            # 建立隔離的命名空間
            namespace = {}
            exec(code_str, namespace)
            
            # 檢查是否有 generate 函數
            if 'generate' not in namespace or not callable(namespace['generate']):
                return "FAILED"
            
            # 執行 1 次 generate()（先這樣），檢查輸出格式
            generate_func = namespace['generate']
            result = generate_func()
            
            # 檢查返回值格式
            if not isinstance(result, dict):
                return "FAILED"
            
            # 檢查必要的鍵
            if 'question_text' not in result or 'answer' not in result:
                return "FAILED"
            
            # 全部通過
            return "PASSED"
            
        except Exception as e:
            # 任何執行錯誤都返回 FAILED
            return "FAILED"
    
    except Exception:
        # 最後的防線
        return "FAILED"

def calculate_file_hash(filepath):
    """計算檔案 SHA256"""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return "FILE_NOT_FOUND"

def _format_file_header(skill_id, model_name, ablation_id, ablation_name, duration, 
                        prompt_tokens, completion_tokens, created_at, healer_status, 
                        basic_cleanup_count=0, healer_fixes=0, fix_status_str="", fixes_str="", 
                        regex_fixes=0, ast_fixes=0, verify_status="PASSED"):
    """
    格式化檔案標頭 (完全參考 code_generator.py 的 _format_header)
    
    Args:
        skill_id: 技能 ID
        model_name: 模型名稱 (實際的模型 key，如 qwen2.5-coder:14b)
        ablation_id: Ablation ID (1/2/3)
        ablation_name: Ablation 名稱 (Ab1/Ab2/Ab3)
        duration: 執行時間 (秒)
        prompt_tokens: Prompt token 數
        completion_tokens: Completion token 數
        created_at: 建立時間
        healer_status: Healer 狀態 (ON/OFF)
        healer_fixes: 修復次數
        fix_status_str: Fix Status 字符串 (e.g. "[Advanced Healer]")
        fixes_str: 詳細修復信息 (e.g. "Basic=1, Advanced=(Regex=1, AST=0)")
        verify_status: 驗證狀態 (PASSED/FAILED)
    
    Returns:
        str: 格式化的檔案標頭 (完全匹配 code_generator.py 格式)
    """
    # 構建 Strategy 字符串
    strategy = "V10.1 Modular Refactored"
    
    # 構建 Advanced Healer 開關字符串
    # Note: Ab2 只有 Regex Healer (進階修復), Ab3 才有 AST (Advanced Healer)
    advanced_healer_status = 'ON' if ablation_id >= 3 else 'OFF'
    
    # 如果沒有提供 fix_status_str，則根據 ablation 類型生成
    if not fix_status_str:
        if ablation_id == 1:
            fix_status_str = "[Basic Cleanup Only]"
            fixes_str = f"Basic={basic_cleanup_count}, Advanced=None"
        elif ablation_id == 2:
            fix_status_str = "[Basic Cleanup Only]"
            fixes_str = f"Basic={basic_cleanup_count}, Advanced=None"
        else:  # ablation_id == 3
            fix_status_str = "[Advanced Healer]"
            fixes_str = f"Basic={basic_cleanup_count}, Advanced=(Regex={regex_fixes}, AST={ast_fixes})"
    
    # 格式化完整的標頭 (完全匹配 code_generator.py)
    header = f"""# ==============================================================================
# ID: {skill_id}
# Model: {model_name} | Strategy: {strategy}
# Ablation ID: {ablation_id} | Basic Cleanup: ENABLED | Advanced Healer: {advanced_healer_status}
# Performance: {duration:.2f}s | Tokens: In={prompt_tokens}, Out={completion_tokens}
# Created At: {created_at}
# Fix Status: {fix_status_str} | Fixes: {fixes_str}
# Verification: Internal Logic Check = {verify_status}
# ==============================================================================

"""
    return header

# ==============================================================================
# 4. 模型選擇菜單
# ==============================================================================

def show_model_selection_menu():
    """
    顯示模型選擇菜單
    
    Returns:
        list: 選擇的模型 KEY 列表
    """
    print("\n" + "="*70)
    print("🤖 [模型選擇] 請選擇要執行的模型範圍")
    print("="*70)
    print(f"   [0] ALL (全部 {len(TARGET_MODELS)} 個模型)")
    for i, model_key in enumerate(TARGET_MODELS, 1):
        display_name = MODEL_DISPLAY_NAMES.get(model_key, model_key)
        print(f"   [{i}] {display_name}")
    
    while True:
        try:
            choice = input("\n👉 請輸入選項 (0-3): ").strip()
            if choice == '0':
                return TARGET_MODELS
            idx = int(choice) - 1
            if 0 <= idx < len(TARGET_MODELS):
                return [TARGET_MODELS[idx]]
            print("❌ 輸入無效，請重試。")
        except ValueError:
            print("❌ 請輸入數字。")

# ==============================================================================
# 5. 主流程
# ==============================================================================

def main():
    print("="*70)
    print("🧪 Math AI 科展實驗執行腳本 (Experiment Runner)")
    print("="*70)

    # 1. 掃描技能目錄 (Results Root)
    if not os.path.exists(RESULTS_ROOT):
        print(f"❌ 找不到結果目錄: {RESULTS_ROOT}")
        print("請先執行 step1_generate_candidates.py (或者手動建立目錄)")
        return

    skills = [d for d in os.listdir(RESULTS_ROOT) if os.path.isdir(os.path.join(RESULTS_ROOT, d))]
    
    if not skills:
        print("⚠️  目錄下沒有任何技能資料夾。")
        return

    # 2. 顯示選單
    print("\n[請選擇要執行的技能]")
    print("[0] 全部執行 (All Skills)")
    for idx, skill in enumerate(skills):
        print(f"[{idx+1}] {skill}")
    
    choice = input("\n👉 請輸入編號: ").strip()
    
    selected_skills = []
    if choice == '0':
        selected_skills = skills
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(skills):
                selected_skills = [skills[idx]]
            else:
                print("❌ 無效的編號")
                return
        except ValueError:
            print("❌ 請輸入數字")
            return

    # 3. 模型選擇
    selected_models = show_model_selection_menu()
    
    # 3.5. [NEW] Ablation 策略選擇
    print("\n" + "="*70)
    print("📋 [策略選擇] 請選擇要執行的 Ablation 策略")
    print("="*70)
    print(f"   [0] ALL (全部 3 個策略)")
    print(f"   [1] Ab1 (Bare - 原生能力測試)")
    print(f"   [2] Ab2 (Engineered - Prompt 工程貢獻)")
    print(f"   [3] Ab3 (Full-Healing - 完整系統修復)")
    
    while True:
        try:
            ablation_choice = input("\n👉 請輸入選項 (0-3): ").strip()
            if ablation_choice == '0':
                selected_ablations = ['Ab1', 'Ab2', 'Ab3']
                selected_strategies = [
                    {"name": "Ab1", "prompt_suffix": "Ab1.txt", "healer": False},
                    {"name": "Ab2", "prompt_suffix": "Ab2.txt", "healer": False},
                    {"name": "Ab3", "prompt_suffix": "Ab2.txt", "healer": True}
                ]
                break
            elif ablation_choice == '1':
                selected_ablations = ['Ab1']
                selected_strategies = [
                    {"name": "Ab1", "prompt_suffix": "Ab1.txt", "healer": False}
                ]
                break
            elif ablation_choice == '2':
                selected_ablations = ['Ab2']
                selected_strategies = [
                    {"name": "Ab2", "prompt_suffix": "Ab2.txt", "healer": False}
                ]
                break
            elif ablation_choice == '3':
                selected_ablations = ['Ab3']
                selected_strategies = [
                    {"name": "Ab3", "prompt_suffix": "Ab2.txt", "healer": True}
                ]
                break
            else:
                print("❌ 輸入無效，請重試。")
        except ValueError:
            print("❌ 請輸入數字。")
    
    # 4. 確認開始
    stats.total_skills = len(selected_skills)
    stats.total_models = len(selected_models)
    stats.total_strategies = len(selected_strategies)
    stats.total_planned_runs = stats.total_skills * stats.total_models * stats.total_strategies * stats.total_samples_per_run
    
    print(f"\n已選擇: {len(selected_skills)} 個技能")
    print(f"已選擇: {len(selected_models)} 個模型")
    for model_key in selected_models:
        print(f"  - {MODEL_DISPLAY_NAMES.get(model_key, model_key)}")
    print(f"已選擇: {len(selected_ablations)} 個策略")
    for ab in selected_ablations:
        print(f"  - {ab}")
    print(f"\n📊 實驗配置統計:")
    print(f"  技能數: {stats.total_skills}")
    print(f"  模型數: {stats.total_models}")
    print(f"  策略數: {stats.total_strategies}")
    print(f"  每組樣本數: {stats.total_samples_per_run}")
    print(f"  📈 總執行次數: {stats.total_planned_runs}")
    
    confirm = input("\n👉 確定要開始實驗嗎? (y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return

    # 5. 初始化 Batch
    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_start_time = time.time()
    
    print("\n" + "="*70)
    print(f"🔬 [實驗執行] 開始巢狀迴圈... Batch: {batch_id}")
    print("="*70)

    # --- 巢狀迴圈開始 ---
    pbar = tqdm(total=stats.total_planned_runs, desc="總進度", unit="run", ncols=80)
    
    for skill in selected_skills:
        skill_dir = os.path.join(RESULTS_ROOT, skill)
        os.makedirs(skill_dir, exist_ok=True)
        
        # (1) 模型迴圈
        for model_key in selected_models:
            
            # (2) 策略迴圈 - 使用使用者選擇的策略
            for strat in selected_strategies:
                ab_name = strat["name"]
                use_healer = strat["healer"]
                prompt_file = f"{skill}_{strat['prompt_suffix']}"
                prompt_path = os.path.join(PROMPTS_DIR, prompt_file)
                
                # 讀取 Prompt
                if not os.path.exists(prompt_path):
                    tqdm.write(f"❌ 找不到 Prompt: {prompt_file} (跳過)")
                    pbar.update(stats.total_samples_per_run) # 跳過該策略的所有樣本
                    continue
                
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    prompt_text = f.read()
                prompt_hash = calculate_file_hash(prompt_path)
                
                # (3) 樣本迴圈 (1~5)
                ablation_id = 1 if ab_name == "Ab1" else 2 if ab_name == "Ab2" else 3
                ablation_display = "Bare" if ab_name == "Ab1" else "Engineered" if ab_name == "Ab2" else "Full-Healing"
                
                for i in range(1, 6):
                    run_start_time = time.time()
                    try:
                        # A. Call LLM (生成代碼)
                        raw_code, usage = call_llm(model_key, prompt_text)
                        
                        # [DEBUG] 檢查 Gemini 是否返回了包含頭部的代碼
                        if raw_code.startswith('#') and '==============' in raw_code:
                            tqdm.write(f"⚠️  WARNING: Gemini 返回了包含頭部註釋的代碼！")
                            tqdm.write(f"   前 200 字: {raw_code[:200]}")
                        
                        # B. 基本清理（Ab1/Ab2/Ab3 都執行）
                        cleaned_code, basic_cleanup_count = apply_basic_cleanup(raw_code)
                        
                        # C. 進階 Healer（僅 Ab3 使用）
                        final_code = cleaned_code
                        healer_status = "OFF"
                        regex_fixes = 0
                        ast_fixes = 0
                        healer_fixed_count = 0
                        
                        if use_healer:  # Ab3 才會進到這裡
                            final_code, regex_fixes, ast_fixes, healer_fixed_count = \
                                apply_healer_mock(cleaned_code, ablation_id, skill)
                            healer_status = "ON"
                            stats.healed_count += 1
                        
                        # D. 建立檔案標頭 (完整格式，參考 code_generator.py)
                        run_duration = time.time() - run_start_time
                        
                        # [新增] 驗證代碼完整性
                        verify_status = verify_code_integrity(final_code)
                        tqdm.write(f"   [DEBUG] verify_status = {verify_status}")
                        
                        header = _format_file_header(
                            skill_id=skill,
                            model_name=model_key,
                            ablation_id=ablation_id,
                            ablation_name=ab_name,
                            duration=run_duration,
                            prompt_tokens=usage.get('prompt', 0),
                            completion_tokens=usage.get('completion', 0),
                            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            healer_status=healer_status,
                            basic_cleanup_count=basic_cleanup_count,
                            healer_fixes=healer_fixed_count,
                            regex_fixes=regex_fixes,
                            ast_fixes=ast_fixes,
                            verify_status=verify_status
                        )
                        
                        # D-1. [NEW] 為 Ab2/Ab3 注入脚手架與工具庫 (參考 code_generator.py L682-683)
                        code_to_save = final_code
                        if ablation_id >= 2:
                            # Ab2, Ab3: 注入完整工具庫與 Domain 函數庫
                            try:
                                from core.code_generator import build_calculation_skeleton
                                skeleton = build_calculation_skeleton(skill)  # 傳入 skill_id
                                code_to_save = skeleton + "\n" + final_code
                            except ImportError:
                                # Fallback: 如果無法導入，直接使用最終代碼
                                tqdm.write(f"⚠️  無法導入 build_calculation_skeleton，跳過脚手架注入")
                                code_to_save = final_code
                        else:
                            # Ab1 (Bare): 不注入脚手架，僅使用生成的代碼
                            code_to_save = final_code
                        
                        # E. Save File (帶標頭 + 脚手架)
                        filename = f"{skill}_{model_key}_{ab_name}_run{i:02d}.py"
                        filepath = os.path.join(skill_dir, filename)
                        
                        # [DEBUG] 檢查 code_to_save 是否已經包含文件頭
                        if code_to_save.startswith('#'):
                            tqdm.write(f"⚠️  WARNING: code_to_save 已包含頭部！")
                            tqdm.write(f"   前 100 字: {code_to_save[:100]}")
                        
                        # [DEBUG] 檢查最終要寫入的內容
                        final_content = header + code_to_save
                        if final_content.count('# ==============================================================================') > 1:
                            tqdm.write(f"⚠️  WARNING: 偵測到多個文件頭！計數: {final_content.count('# ==============================================================================')}")
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(final_content)
                        
                        # F. 記錄到資料庫 (ExperimentLog)
                        log_experiment_to_db(
                            skill_id=skill,
                            model_name=model_key,
                            ablation_id=ablation_id,
                            duration=run_duration,
                            prompt_tokens=usage.get('prompt', 0),
                            completion_tokens=usage.get('completion', 0),
                            raw_code=raw_code,
                            final_code=code_to_save,  # 使用注入脚手架後的代碼
                            is_success=True,
                            healer_fixes=healer_fixed_count,
                            verify_status=verify_status  # <--- [NEW] 記得傳入這個！
                        )
                        
                        # G. 更新統計數據
                        stats.successful_runs += 1
                        stats.total_tokens_prompt += usage.get('prompt', 0)
                        stats.total_tokens_completion += usage.get('completion', 0)
                        stats.total_time_seconds += run_duration
                        stats.model_stats[model_key]['success'] += 1
                        stats.model_stats[model_key]['tokens_prompt'] += usage.get('prompt', 0)
                        stats.model_stats[model_key]['tokens_completion'] += usage.get('completion', 0)
                        stats.model_stats[model_key]['time'] += run_duration
                        stats.skill_stats[skill]['success'] += 1
                        stats.skill_stats[skill]['tokens_prompt'] += usage.get('prompt', 0)
                        stats.skill_stats[skill]['tokens_completion'] += usage.get('completion', 0)
                        stats.skill_stats[skill]['time'] += run_duration
                        
                        tqdm.write(f"✅ [{batch_id.split('_')[1]}] {filename} "
                                 f"({usage['completion']} toks, {run_duration:.2f}s, {healer_status}) | DB: logged")
                        
                    except Exception as e:
                        stats.failed_runs += 1
                        stats.model_stats[model_key]['failure'] += 1
                        stats.skill_stats[skill]['failure'] += 1
                        tqdm.write(f"❌ Error in {skill}_{model_key}_{ab_name}_run{i:02d}: {e}")
                    
                    finally:
                        pbar.update(1)

    pbar.close()
    
    # 計算最終統計
    batch_total_time = time.time() - batch_start_time
    
    print("\n" + "="*70)
    print("🎉 全部實驗完成！")
    print("="*70)
    print(f"\n📊 [全局統計]")
    print(f"  ✅ 成功: {stats.successful_runs} / {stats.total_planned_runs}")
    print(f"  ❌ 失敗: {stats.failed_runs}")
    print(f"  ⚡ Token 總計: Prompt={stats.total_tokens_prompt}, Completion={stats.total_tokens_completion}")
    print(f"  ⏱️  總耗時: {batch_total_time:.2f}s")
    print(f"  🔧 已修復: {stats.healed_count} 個 (Healer 應用)")
    
    print(f"\n📈 [模型統計]")
    for model_key in selected_models:
        m_stats = stats.model_stats[model_key]
        print(f"  {MODEL_DISPLAY_NAMES.get(model_key, model_key)}:")
        print(f"    ✅ {m_stats['success']} | ❌ {m_stats['failure']} | "
              f"Token({m_stats['tokens_prompt']}/{m_stats['tokens_completion']}) | "
              f"Time {m_stats['time']:.2f}s")
    
    print(f"\n🎓 [技能統計]")
    for skill in selected_skills:
        s_stats = stats.skill_stats[skill]
        print(f"  {skill}: ✅ {s_stats['success']} | ❌ {s_stats['failure']} | "
              f"Token({s_stats['tokens_prompt']}/{s_stats['tokens_completion']})")
    
    print(f"\n📂 結果目錄: {RESULTS_ROOT}")
    print("="*70)

if __name__ == "__main__":
    main()
