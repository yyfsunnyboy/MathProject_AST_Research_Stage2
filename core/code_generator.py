#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ============================================================================== 
# ID: code_generator.py
# Version: V10.1.0 (Modular Refactored Edition)
# Last Updated: 2026-01-31
# Author: Math AI Research Team (Advisor & Student)
#
# [Description]:
#   本模組為科展實驗的自動技能生成核心，負責根據規格書自動產生技能程式碼，
#   並支援 AST/Regex 修復、沙盒驗證等功能，確保生成結果符合標準。
#
#   [Scientific Control Strategy]:
#   本模組配合「單一黃金標準」策略，確保所有技能生成均以統一規格書為依據，
#   以利不同模型、Ablation 組別間的公平比較與統計分析。
#
# [Key Functions]:
#   1. auto_generate_skill_code: 主入口，根據技能 ID 與實驗參數自動生成技能程式碼。
#   2. ast_fix_code: 進行 AST 結構修復，提升程式碼健壯性。
#   3. validate_skill_code: 執行沙盒驗證，確保生成程式碼可正確運作。
#
# [Database Schema Usage]:
#   - 讀取: SkillGenCodePrompt (獲取標準規格書)
#   - 寫入: experiment_log (記錄生成過程與修復次數)
#   - 寫入: Local File System (儲存最終技能程式碼)
#
# [Logic Flow]:
#   1. 讀取目標技能規格書
#   2. 生成初版程式碼
#   3. 執行 AST/Regex 修復（依 Ablation 設定）
#   4. 沙盒驗證與評分
#   5. 寫入實驗日誌與技能檔案
# ============================================================================== 

import os
import time
import datetime
import re
import textwrap
import importlib.util
import sqlite3
import random
import math
import ast
import operator
from fractions import Fraction
from pathlib import Path

# Local Imports
# (Ensure PYTHONPATH includes the project root)
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from core.ai_wrapper import get_ai_client
from models import SkillGenCodePrompt, ExperimentLog, db, SkillInfo, TextbookExample, AblationSetting

from core.healers.regex_healer import RegexHealer
from core.healers.ast_healer import ASTHealer
from core.prompts.prompt_builder import PromptBuilder
from core.validators.code_validator import validate_python_code as _validate_python_code
from core.validators.dynamic_sampler import DynamicSampler
from core.code_utils.file_utils import ensure_dir, path_in_root
from core.code_utils.math_utils import *
from core.code_utils.latex_utils import *

REFACTOR_MODULES_AVAILABLE = True

def _build_prompt(skill_id, ablation_id, db_master_spec):
    """根據 ablation_id 構建 prompt (委派給 PromptBuilder)"""
    # 這裡直接調用 PromptBuilder，保持向後兼容
    prompt = PromptBuilder.build(db_master_spec, ablation_id=ablation_id, skill_id=skill_id)
    topic = ""  # 可根據需要擴充
    textbook_example = ""  # 可根據需要擴充
    return prompt, topic, textbook_example

def _call_ai(prompt):
    """呼叫 AI 並回傳 raw_output, prompt_tokens, completion_tokens"""
    client = get_ai_client(role='coder')
    response = client.generate_content(prompt)
    
    # 處理各種可能的 Response 格式
    raw_output = ""
    prompt_tokens = 0
    completion_tokens = 0
    
    if hasattr(response, 'text'):
        raw_output = response.text
    elif hasattr(response, 'content'): 
        raw_output = response.content
    else:
        raw_output = str(response)

    try:
        if hasattr(response, 'usage_metadata'):
            prompt_tokens = response.usage_metadata.prompt_token_count
            completion_tokens = response.usage_metadata.candidates_token_count
        elif hasattr(response, 'usage'):
             prompt_tokens = response.usage.prompt_tokens
             completion_tokens = response.usage.completion_tokens
    except:
        pass
        
    return raw_output, prompt_tokens, completion_tokens

def _validate_code(final_code):
    """語法驗證"""
    return _validate_python_code(final_code)

def _dynamic_sampling(final_code):
    """
    動態採樣驗證 generate() 輸出 (Process-Isolated + Timeout 防止死迴圈)
    """
    import subprocess
    import sys
    import uuid
    import json
    
    dyn_ok = True
    sampling_success_count = 0
    sampling_total_count = 0
    error_msg = ''
    
    try:
        # 1. 準備臨時目錄與檔案
        root = path_in_root()
        temp_dir = ensure_dir(os.path.join(root, 'temp'))
        unique_id = uuid.uuid4().hex[:8]
        temp_filename = f"dyn_sample_{unique_id}.py"
        temp_path = os.path.join(temp_dir, temp_filename)
        wrapper_filename = f"wrapper_{unique_id}.py"
        wrapper_path = os.path.join(temp_dir, wrapper_filename)

        # 2. 寫入目標代碼
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(final_code)
            
        # 3. 寫入 Wrapper 腳本
        # 確保路徑轉義這用於生成的 Python 字串中
        root_escaped = root.replace('\\', '/')
        temp_path_escaped = temp_path.replace('\\', '/')
        
        wrapper_code = f"""import sys
import os
import json
import importlib.util

# Add project root needed for imports
sys.path.append('{root_escaped}')

try:
    # Load the module dynamically from file path
    spec = importlib.util.spec_from_file_location("temp_mod", r"{temp_path_escaped}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    if not hasattr(module, 'generate'):
        print(json.dumps({{'status': 'error', 'msg': 'Function generate not found'}}))
        sys.exit(0)
        
    for i in range(3):
        res = module.generate()
        if not isinstance(res, dict) or 'question_text' not in res or 'answer' not in res:
             print(json.dumps({{'status': 'error', 'msg': 'Invalid return format'}}))
             sys.exit(0)
             
    print(json.dumps({{'status': 'ok'}}))
    
except Exception as e:
    print(json.dumps({{'status': 'error', 'msg': str(e)}}))
"""
        with open(wrapper_path, 'w', encoding='utf-8') as f:
            f.write(wrapper_code)
            
        # 4. 執行子進程 (Timeout = 5秒)
        proc = subprocess.run(
            [sys.executable, wrapper_path],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=root
        )
        
        stdout_output = proc.stdout.strip()
        
        if proc.returncode != 0:
            dyn_ok = False
            error_msg = f"Runtime Error: {proc.stderr or stdout_output}"
        else:
            try:
                # 嘗試解析最後一行的 JSON
                lines = stdout_output.splitlines()
                last_line = lines[-1] if lines else "{}"
                res = json.loads(last_line)
                
                if res.get('status') == 'ok':
                    sampling_success_count = 3
                    sampling_total_count = 3
                else:
                    dyn_ok = False
                    error_msg = res.get('msg', 'Unknown Logic Error')
            except json.JSONDecodeError:
                dyn_ok = False
                error_msg = f"JSON Parse Failed. Output: {stdout_output}"
                
    except subprocess.TimeoutExpired:
        dyn_ok = False
        error_msg = "TIMEOUT: Code generation took > 5s (Infinite Loop Detected)"
        
    except Exception as e:
        dyn_ok = False
        error_msg = f"System Error: {str(e)}"
        
    finally:
        # 清理臨時檔案
        try:
            if os.path.exists(temp_path): os.remove(temp_path)
            if os.path.exists(wrapper_path): os.remove(wrapper_path)
        except:
            pass
            
    return dyn_ok, sampling_success_count, sampling_total_count, error_msg

def _format_header(skill_id, current_model, ablation_id, duration, prompt_tokens, completion_tokens, created_at, fix_status_str, fixes_str, verify_status_str):
    """產生檔案標頭"""
    header = f"""# ==============================================================================\n# ID: {skill_id}\n# Model: {current_model} | Strategy: V10.1 Modular Refactored\n# Ablation ID: {ablation_id} | Basic Cleanup: ENABLED | Advanced Healer: {'ON' if ablation_id>=2 else 'OFF'}\n# Performance: {duration:.2f}s | Tokens: In={prompt_tokens}, Out={completion_tokens}\n# Created At: {created_at}\n# Fix Status: {fix_status_str} | Fixes: {fixes_str}\n# Verification: Internal Logic Check = {verify_status_str}\n# ==============================================================================\n"""
    return header

def _write_file(out_path, header, final_code):
    ensure_dir(os.path.dirname(out_path))
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(header + final_code)

def _log_experiment(**kwargs):
    """Log to DB"""
    try:
        log_entry = ExperimentLog(
            skill_id=kwargs.get('skill_id'),
            start_time=kwargs.get('start_time'),
            duration_seconds=time.time() - kwargs.get('start_time', time.time()),
            prompt_len=kwargs.get('prompt_len'),
            code_len=kwargs.get('code_len'),
            is_success=kwargs.get('is_valid'),
            error_msg=kwargs.get('error_msg'),
            repaired=kwargs.get('repaired'),
            model_name=kwargs.get('model_name'),
            prompt_tokens=kwargs.get('prompt_tokens'),
            completion_tokens=kwargs.get('completion_tokens'),
            total_tokens=kwargs.get('total_tokens'),
            ablation_id=kwargs.get('ablation_id'),
            raw_response=kwargs.get('raw_response'),
            final_code=kwargs.get('final_code')
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        print(f"Error logging experiment: {e}")
        try:
            db.session.rollback()
        except:
            pass

def _basic_cleanup(code):
    """移除 markdown 標記"""
    old_code = code
    code = re.sub(r'^(\s*)```python\s*\n', '', code, flags=re.MULTILINE)
    code = re.sub(r'^(\s*)```\s*\n', '', code, flags=re.MULTILINE)
    code = re.sub(r'\n(\s*)```\s*$', '', code, flags=re.MULTILINE)
    code = code.strip()
    return code, 1 if code != old_code else 0


def _advanced_healer(clean_code, ablation_id, skill_id):
    """進階 Healer：委派給 RegexHealer 與 ASTHealer"""
    # Regex 修復
    regex_healer = RegexHealer()
    code_after_regex, regex_fixes = regex_healer.heal(clean_code)
    
    # AST 修復
    ast_healer = ASTHealer()
    try:
        code_after_ast, ast_fixes = ast_healer.heal(code_after_regex)
    except Exception as e:
        print(f"🔧 [{skill_id}] AST Healing Failed: {e}")
        
        # [NEW] Fail-fast for Ablation 3
        # Ab3 的核心價值在於 AST Healer，如果失敗就不應該執行
        if ablation_id == 3:
            print(f"⚠️ [Safety] Ab3 AST 解析失敗，為防止無窮迴圈，將使用 Regex 修復後的代碼")
            print(f"   如果代碼有無窮迴圈，會在動態採樣階段被 timeout 機制攔截")
            # 返回 Regex 修復後的代碼，不要完全失敗
            code_after_ast = code_after_regex
            ast_fixes = 0
        else:
            code_after_ast = code_after_regex
            ast_fixes = 0
    
    # 這裡可擴充更多修復統計資訊
    garbage_cleaner_count = 0
    removed_list = []
    healer_fixes = regex_fixes + ast_fixes
    eval_eliminator_count = 0
    healing_duration = 0
    
    return code_after_ast, regex_fixes, ast_fixes, garbage_cleaner_count, removed_list, healer_fixes, eval_eliminator_count, healing_duration


def _post_ast_fixes(clean_code, skill_id):
    """F.12/F.13/F.14 Post-AST Fixes (暫時直接回傳，若有特殊後處理可委派到 healers)"""
    # 若有特殊後處理需求，可在 healers/ast_healer.py 中擴充
    qwen_fixes = 0
    return clean_code, qwen_fixes

def auto_generate_skill_code(skill_id, queue=None, **kwargs):
    start_time = time.time()
    role_config = Config.MODEL_ROLES.get('coder', {'provider': 'google', 'model': 'gemini-1.5-flash'})
    current_model = role_config.get('model', 'Unknown')
    ablation_id = kwargs.get('ablation_id', 3)
    
    # Ablation Settings
    ablation_config = AblationSetting.query.get(ablation_id)
    if ablation_config:
        use_regex_healer = ablation_config.use_regex
        use_ast_healer = ablation_config.use_ast
        ablation_name = ablation_config.name
    else:
        use_regex_healer = (ablation_id >= 2)
        use_ast_healer = (ablation_id >= 3)
        ablation_name = f"Ablation-{ablation_id}"

    custom_output_path = kwargs.get('custom_output_path', None)
    print(f"\n{'='*70}")
    print(f"🧪 [Ablation {ablation_id}] {ablation_name}")
    print(f"   Regex Healer: {'✅ Enabled' if use_regex_healer else '❌ Disabled'}")
    print(f"   AST Healer:   {'✅ Enabled' if use_ast_healer else '❌ Disabled'}")
    if custom_output_path:
        print(f"   Output: {os.path.basename(custom_output_path)}")
    print(f"{'='*70}\n")
    
    # Get DB Spec
    active_prompt = SkillGenCodePrompt.query.filter_by(skill_id=skill_id, prompt_type="MASTER_SPEC").order_by(SkillGenCodePrompt.created_at.desc()).first()
    db_master_spec = active_prompt.prompt_content if active_prompt else "生成一題簡單的整數四則運算。"
    
    # Prompt 構建
    prompt, topic, textbook_example = _build_prompt(skill_id, ablation_id, db_master_spec)
    
    # AI 生成
    raw_output, prompt_tokens, completion_tokens = _call_ai(prompt)
    
    # 基礎清理
    clean_code, markdown_cleanup_count = _basic_cleanup(raw_output)
    basic_cleanup_fixes = markdown_cleanup_count + 1
    
    regex_fixes = 0
    ast_fixes = 0
    garbage_cleaner_count = 0
    removed_list = []
    healer_fixes = 0
    eval_eliminator_count = 0
    healing_duration = 0
    
    # 進階 Healer
    if use_regex_healer:
        clean_code, regex_fixes, ast_fixes, garbage_cleaner_count, removed_list, healer_fixes, eval_eliminator_count, healing_duration = _advanced_healer(clean_code, ablation_id, skill_id)
        
    # F.12/F.13/F.14 Post-AST Fixes
    clean_code, qwen_fixes = _post_ast_fixes(clean_code, skill_id)
    
    # 組裝 final_code
    if ablation_id >= 2:
        skeleton = build_calculation_skeleton(skill_id)
        final_code = skeleton + "\n" + clean_code
    else:
        # Ab1 (Bare) 這裡也加上 skeleton 確保可運行，或視需求調整
        skeleton = build_calculation_skeleton(skill_id)
        final_code = skeleton + "\n" + clean_code
        
    # 驗證
    is_valid, error_msg = _validate_code(final_code)
    
    # 動態採樣
    dyn_ok, sampling_success_count, sampling_total_count, dyn_error_msg = _dynamic_sampling(final_code) if is_valid else (False, 0, 0, '')
    
    duration = time.time() - start_time
    created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    fix_status_str = "[Advanced Healer]" if (regex_fixes > 0 or ast_fixes > 0) else ("[Basic Cleanup]" if basic_cleanup_fixes > 0 else "[Clean Pass]")
    verify_status_str = "PASSED" if (is_valid and dyn_ok) else "FAILED"
    fixes_str = f"Basic={basic_cleanup_fixes}, Advanced=(Regex={regex_fixes}, AST={ast_fixes})"
    header = _format_header(skill_id, current_model, ablation_id, duration, prompt_tokens, completion_tokens, created_at, fix_status_str, fixes_str, verify_status_str)
    
    # 檔案寫入
    model_size_class = kwargs.get('model_size_class', '14b')
    if custom_output_path:
        out_path = custom_output_path
    else:
        skills_dir = ensure_dir(path_in_root('skills'))
        out_path = os.path.join(skills_dir, f'{skill_id}.py')
        
    try:
        _write_file(out_path, header, final_code)
        print(f"✅ [{skill_id}] File written: {os.path.abspath(out_path)}")
    except Exception as e:
        print(f"❌ [{skill_id}] Failed to write file: {e}")
        
    # Log
    _log_experiment(
        skill_id=skill_id,
        start_time=start_time,
        prompt_len=len(prompt),
        code_len=len(final_code),
        is_valid=is_valid and dyn_ok,
        error_msg=error_msg or dyn_error_msg,
        repaired=(regex_fixes > 0 or ast_fixes > 0),
        model_name=current_model,
        final_code=final_code,
        raw_response=raw_output,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        ablation_id=ablation_id
    )
    
    return is_valid and dyn_ok, "V10.1 Generated", {
        'tokens': prompt_tokens + completion_tokens,
        'score_syntax': 100.0 if (is_valid and dyn_ok) else 0.0,
        'total_fixes': regex_fixes + ast_fixes,
        'regex_fixes': regex_fixes,
        'ast_fixes': ast_fixes,
        'is_valid': is_valid and dyn_ok
    }

# ==============================================================================
# 3. 完美工具庫 (Perfect Utils - Dynamic Builder)
# ==============================================================================

def _build_perfect_utils():
    """
    [V10.1] 動態從新模組中提取工具函數源代碼（簡化版）
    直接讀取檔案並移除模組頭註解，保持代碼完整性
    """
    from pathlib import Path
    
    # 1. 基礎 imports
    base_imports = '''import random
from random import randint, choice
import math
from fractions import Fraction
import re
import ast
import operator

# ✅ 預設的 LaTeX 運算子映射（四則）- 全域可用
op_latex = {'+': '+', '-': '-', '*': '\\\\times', '/': '\\\\div'}

'''
    
    # 2. 動態讀取 code_utils 模組的源代碼
    try:
        # 假設 code_utils 位於 core/code_utils
        current_dir = Path(__file__).parent
        code_utils_dir = current_dir / 'code_utils'
        
        # 簡易檢查：如果當前檔案在 core 下，則 code_utils 就在旁邊
        # 如果路徑錯誤，嘗試調整
        if not code_utils_dir.exists():
            # 嘗試專案根目錄下的 core/code_utils
             pass 

        all_code = []
        
        # 讀取各個工具模組
        for module_file in ['math_utils.py', 'latex_utils.py', 'file_utils.py']:
            file_path = code_utils_dir / module_file
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # 找到第一個函數定義的位置，跳過模組頭
                code_start = 0
                in_docstring = False
                for i, line in enumerate(lines):
                    # 跳過模組級的 docstring
                    if '"""' in line or "'''" in line:
                         if line.count('"""') == 2 or line.count("'''") == 2:
                             continue # 單行docstring
                         in_docstring = not in_docstring
                         continue
                    if in_docstring:
                        continue
                    # 跳過 import 語句和空行
                    if line.strip().startswith('import ') or \
                       line.strip().startswith('from ') or \
                       line.strip() == '' or \
                       line.strip().startswith('#'):
                        continue
                    # 找到第一個函數或類定義
                    if line.strip().startswith('def ') or line.strip().startswith('class '):
                        code_start = i
                        break
                
                # 提取從第一個定義開始的所有代碼
                if code_start > 0:
                    function_code = ''.join(lines[code_start:])
                    all_code.append(function_code)
        
        # 3. 組合完整的 PERFECT_UTILS
        return base_imports + '\n'.join(all_code)
        
    except Exception as e:
        # 降級：如果無法讀取，返回最小集合
        print(f"⚠️  無法動態構建 PERFECT_UTILS: {e}，使用最小集合")
        return base_imports + '''
# [REFACTORED] 已搬移到 code_utils.math_utils
# - safe_choice, to_latex, fmt_num 已在 code_utils 中定義並導入
# 這些函數的完整版本已通過 import 導入，此處不再重複定義
'''

PERFECT_UTILS = _build_perfect_utils()

# ==============================================================================
# 3. 骨架與 Prompt 定義
# ==============================================================================
def build_calculation_skeleton(skill_id=None):
    """
    動態構建代碼框架，根據 skill_id 自動注入對應的 Domain 函數庫
    
    參數:
        skill_id: str, 例如 'gh_ApplicationsOfDerivatives'
    
    返回:
        str: 包含 PERFECT_UTILS + Domain Functions 的完整代碼框架
    """
    skeleton = r'''

# [INJECTED UTILS]
''' + PERFECT_UTILS + r'''
'''
    
    # [V47.14 新增] 動態注入 Domain 函數庫
    if skill_id:
        from core.prompts.domain_function_library import get_required_domains, get_domain_helpers_code
        
        required_domains = get_required_domains(skill_id)
        if required_domains:
            domain_code = get_domain_helpers_code(required_domains)
            skeleton += f'\n# [DOMAIN HELPERS - Auto-Injected for {skill_id}]\n'
            skeleton += domain_code + '\n'
    
    skeleton += r'''

# [AI GENERATED CODE]
# ---------------------------------------------------------
''' + "\n"
    
    return skeleton

# 保留舊的 CALCULATION_SKELETON 常量（向後兼容）
CALCULATION_SKELETON = build_calculation_skeleton()