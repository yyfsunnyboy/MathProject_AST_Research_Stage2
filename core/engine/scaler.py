# -*- coding: utf-8 -*-
import os
import uuid
import random
import time
import sys
import importlib.util
from core.ai_wrapper import get_ai_client, call_ai_with_retry
from core.code_generator import auto_generate_skill_code
from config import Config

class AdaptiveScaler:
    """
    AdaptiveScaler 負責根據技能與難度生成題目。
    採用 JIT (Just-in-Time) 模式：根據需求動態生成並執行出題腳本。
    """
    def __init__(self, model_role='generator'):
        self.model_role = model_role
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def _get_skill_path(self, skill_name):
        return os.path.join(self.project_root, "agent_skills", skill_name)

    def generate_problem(self, skill_name, level=2):
        """
        生成指定技能與難度的題目。
        Args:
            skill_name: 技能名稱 (例如 jh_數學2上_FourOperationsOfRadicals)
            level: 1 (Easy), 2 (Normal), 3 (Hard)
        Returns:
            dict: 包含題目的字典
        """
        skill_path = self._get_skill_path(skill_name)
        skill_md_path = os.path.join(skill_path, "SKILL.md")
        
        if not os.path.exists(skill_md_path):
            raise FileNotFoundError(f"找不到技能定義: {skill_md_path}")

        difficulty_names = {1: "EASY (簡單)", 2: "NORMAL (標準)", 3: "HARD (進階/挑戰)"}
        print(f"🚀 正在為 {skill_name} 生成 {difficulty_names.get(level)} 等級的題目代碼...")
        
        # 使用 auto_generate_skill_code
        # 它會回傳一個結果路徑或狀態
        try:
            # 這裡我們利用 ablation_id=2 (Regex Healed)
            # auto_generate_skill_code 會將檔案寫入 agent_tools/reports/...
            # 我們需要抓到它是哪一個檔案
            from core.code_utils.file_utils import ensure_dir
            
            # [Optimization] 這裡我們直接傳入 level 參數作為 kwargs，
            # 但目前的 auto_generate_skill_code 可能不會直接把 level 傳給 AI。
            # 沒關係，SKILL.md 裡面的 generate(level) 會處理。
            
            # 執行生成
            # 注意：auto_generate_skill_code 會回傳生成的 code 字串 (在 V50.0 版本中是有回傳的嗎？)
            # 讓我們檢查一下 auto_generate_skill_code 的定義。
            # 根據 outline，它回傳的可能是成果路徑。
            
            # 這裡我們做一個簡化：直接呼叫後，從回傳或生成的路徑讀取。
            # 但為了效率，我們可以直接從 generate_skill_code 邏輯中提取。
            
            # 其實，我們可以更直接一點：因為我們要的是「執行」，
            # 我們可以直接呼叫 auto_generate_skill_code，然後它會存檔。
            # 然後我們再去載入那個檔。
            
            # [修正] 其實在 V50.0 版本的 code_generator 中，
            # auto_generate_skill_code 的實作會把檔案存在特定的 report 目錄下。
            
            # 為了測試，我們先假設它能運作。
            # 如果要更精準，我應該檢查 auto_generate_skill_code 的回傳值。
            
            # [Hack] 這裡我改用更底層的 _build_prompt + _call_ai + _basic_cleanup 
            # 這樣可以直接拿到 code 字串。
            
            from core.code_generator import _build_prompt, _call_ai, _basic_cleanup, _advanced_healer, _inject_domain_libs
            
            # 1. 構建 Prompt
            # 這裡我們讀取 SKILL.md 並與骨架結合
            # 簡化起見，我們借用 code_generator 的內部邏輯
            
            # 讀取 SKILL.md
            with open(skill_md_path, "r", encoding="utf-8") as f:
                skill_spec = f.read()
            
            # 呼叫 AI (這裡我們跳過 DB logging，直接拿 code)
            prompt = f"{skill_spec}\n\n【特別要求】請生成難度為 {difficulty_names.get(level)} 的題目內容。"
            
            # [Fix] 使用 Qwen3-8B 作為預設發案模型
            from config import Config
            model_config = Config.CODER_PRESETS.get('qwen3-8b')
            raw_code, _, _ = _call_ai(prompt, model_config=model_config)
            
            # 2. 清理與修復
            # [Fix] _basic_cleanup 回傳的是 (code, fixes_count)
            clean_code, _ = _basic_cleanup(raw_code)
            
            # [Fix] 預設使用 ablation_id=3 (AST Healed) 以獲得最高成功率
            healed_code, *healer_stats = _advanced_healer(clean_code, ablation_id=3, skill_id=skill_name)
            
            # 3. 注入 Libs
            # [Fix] _inject_domain_libs 回傳的是 (code, injected_list)
            final_code, _ = _inject_domain_libs(healed_code)
            
            return self._execute_code(final_code, level)

        except Exception as e:
            import traceback
            traceback.print_exc()
            raise Exception(f"代碼生成或執行失敗: {e}")

    def generate_custom_problems(self, skill_name, input_text, count=5, model_id='qwen3-8b', ablation_mode=False):
        """
        根據輸入例題，完全模仿題型生成 count 題。
        ablation_mode: 若為 True (Ab1 模式)，跳過 SKILL.md 讀取與 Healer 修復，使用原生 Prompt。
        """
        # 1. 根據您的正確清單進行資源定位 (Domain Mapping)
        domain_config = {
            "OfIntegers": "IntegerOps",
            "OfNumbers": "FractionOps",
            "OfPolynomial": "PolynomialOps",
            "OfRadicals": "RadicalOps"
        }
        
        target_ops = "IntegerOps" # 預設
        for key, val in domain_config.items():
            if key in skill_name:
                target_ops = val
                break
                
        try:
            from core.code_generator import _call_ai, _basic_cleanup, _advanced_healer, _inject_domain_libs
            
            if ablation_mode:
                print(f"⚠️ [Ab1] 載入 {skill_name} Baseline Prompt。")
                skill_path = self._get_skill_path(skill_name)
                ab1_prompt_path = os.path.join(skill_path, "experiments", "ab1_bare_prompt.md")
                if os.path.exists(ab1_prompt_path):
                    with open(ab1_prompt_path, "r", encoding="utf-8") as f:
                        ab1_template = f.read()
                    import re
                    # 使用正則替換【參考例題】區塊，把題目換成我們提供的 input_text
                    prompt = re.sub(
                        r"【參考例題】.*?【程式要求】", 
                        f"【參考例題】\n{input_text}\n\n【程式要求】", 
                        ab1_template, 
                        flags=re.DOTALL
                    )
                else:
                    prompt = f"請寫一個 generate(level=1) 函式，參考：\n{input_text}\n直接輸出代碼。"
                active_ablation_id = 1
            else:
                print(f"🚀 [Ab3] 鎖定 {skill_name} 基因庫...")
                skill_path = self._get_skill_path(skill_name)
                skill_md_path = os.path.join(skill_path, "SKILL.md")
                if not os.path.exists(skill_md_path):
                    raise FileNotFoundError(f"找不到技能定義: {skill_md_path}")
                with open(skill_md_path, "r", encoding="utf-8") as f:
                    raw_text = f.read()
                    # 徹底消除 Windows CRLF 導致的 f-string 游標回車覆寫問題
                    full_skill_spec = "\n".join([line.replace('\r', '') for line in raw_text.splitlines()])

                # 使用明確的切斷錨點，確保不同技能都能精準抓取精華區塊
                skill_spec_distilled = full_skill_spec.split("【完整程式碼】")[0].strip()

                if ablation_mode:
                    prompt = f"""{skill_spec_distilled}

請參考以下例題，撰寫一個 `generate(level=1)` 函式：
{input_text}
直接輸出代碼。
"""
                else:
                    # 預處理 input_text 確保有 LaTeX 基本結構
                    input_text_safe = self._sanitize_input_dna(input_text)
                    
                    # 神盾級縮減 Prompt (JIT 版) 適用於所有 Ab3 模型
                    prompt = f"""{skill_spec_distilled}
【JIT DNA 任務】模仿例題結構撰寫 `generate(level=1, **kwargs)`。
【目標例題 DNA】: {input_text_safe}

【⚠️ 資源鎖定憲法】
1. 嚴禁寫出 `if level == ...` 結構。
2. 必須 使用 `{target_ops}` 的 static methods 計算與格式化。
3. 渲染：題目用 `{target_ops}.format_latex`，答案用 `{target_ops}.format_plain`。
4. 進階：如果例題項次亂序，題目必須呼叫 `{target_ops}.format_shuffled_latex`。
5. 初始化防護：函式第一行必須先定義 `question_text = ""`。
6. 輸出：只需產出從 `import random` 開始的 Python 代碼，禁止任何註解或解釋文字。

[⚠️ 格式轉換命令]
1. 偵測輸入：即使例題 DNA 是以純文字（如 ^2）表示，你也必須將其視為數學結構。
2. 強制轉換：生成的題目【必須】使用 `{target_ops}.format_latex()` 進行渲染。
3. 嚴禁：嚴禁在 `question_text` 中直接寫出 `^2` 或 `x2` 等非 LaTeX 符號。
"""
                active_ablation_id = 3
            
            from config import Config
            model_config = Config.CODER_PRESETS.get(model_id) or Config.CODER_PRESETS.get('qwen3-8b')
            
            start_ai = time.time()
            raw_code, _, _, thinking_text = _call_ai(prompt, model_config=model_config)
            ai_inference_time_sec = time.time() - start_ai
            
            clean_code, _ = _basic_cleanup(raw_code)
            
            if ablation_mode:
                # [完全跳過 Healer] Ab1 實驗精神：只做基礎字串清理，保留 AI 生成的所有原生邏輯錯誤/套件缺失
                final_code = clean_code
                healed_code = clean_code
                regex_fixes = 0
                ast_fixes = 0
                class DummyASTStats:
                    pass
                dummy_stats = DummyASTStats()
                dummy_stats.logs = []
                healer_stats = [dummy_stats]
                print("⚠️ [Ab1 模式] 已繞過 _advanced_healer 與 _inject_domain_libs。")
            else:
                # [執行完整 Healer + 函式庫注入]
                healed_code, *healer_stats = _advanced_healer(clean_code, ablation_id=active_ablation_id, skill_id=skill_name)
                
                # [核心優化]：在代碼中注入可見的修復痕跡
                healed_code = self._inject_healer_tags(healed_code, raw_code, target_ops)
                
                final_code, _ = _inject_domain_libs(healed_code)
                regex_fixes = healer_stats[0] if len(healer_stats) > 0 else 0
                ast_fixes = healer_stats[1] if len(healer_stats) > 1 else 0
            
            print("\n=== DEBUG: GENERATED CODE ===")
            print(final_code)
            print("=============================\n")
            
            # [修正] 這裡直接使用頂層 os
            save_dir = "generated_scripts"
            if not os.path.exists(save_dir):
                os.makedirs(save_dir, exist_ok=True)
                
            unique_filename = f"live_show_{int(time.time())}_{uuid.uuid4().hex[:6]}.py"
            file_path = os.path.join(save_dir, unique_filename)
            
            with open(file_path, "w", encoding="utf-8") as _fb:
                _fb.write(final_code)
            
            # MCRI Report - Code Robustness
            robustness_grade = "UNKNOWN"
            robustness_reason = ""
            try:
                from scripts.evaluate_mcri import analyze_code_robustness, evaluate_math_hygiene
                robustness_grade, robustness_reason = analyze_code_robustness(healed_code)
            except ImportError:
                pass
            
            # 拿到 final_code 後，執行 count 次
            start_cpu = time.time()
            results = []
            for i in range(count):
                try:
                    res = self._execute_code(final_code, level=1) # pass dummy level 1
                    
                    # 計算 MCRI Math Hygiene
                    if "question_text" in res:
                        try:
                            h_score, h_notes = evaluate_math_hygiene(res["question_text"])
                            res["_mcri_hygiene_score"] = h_score
                            res["_mcri_hygiene_notes"] = h_notes
                        except:
                            pass
                            
                    results.append(res)
                except Exception as e:
                    results.append({"error": f"執行第 {i+1} 題時發生錯誤: {e}"})
            cpu_execution_time_sec = time.time() - start_cpu
            
            debug_meta = {
                "prompt": prompt,
                "raw_text": raw_code,  # 提供給前端失敗時展示
                "raw_code": raw_code,
                "thinking": thinking_text,
                "final_code": final_code,
                "file_path": file_path,
                "healer_trace": {
                    "regex_fixes": regex_fixes,
                    "ast_fixes": ast_fixes
                },
                "mcri_report": {
                    "robustness_grade": robustness_grade,
                    "robustness_reason": robustness_reason
                },
                "bare_prompt": prompt if ablation_mode else "",
                "scaffold_prompt": prompt if not ablation_mode else "",
                "healer_logs": getattr(healer_stats[-1], "logs", []) if healer_stats and hasattr(healer_stats[-1], "logs") else [],
                "performance": {
                    "ai_inference_time_sec": round(ai_inference_time_sec, 2),
                    "cpu_execution_time_sec": round(cpu_execution_time_sec, 4)
                }
            }
            
            return {
                "problems": results,
                "debug_meta": debug_meta
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            raise Exception(f"代碼生成或執行失敗: {e}")

    def _sanitize_input_dna(self, text):
        import re
        # 1. 處理平方：將 x^2 轉為 x^{2} (LaTeX 標準)
        text = re.sub(r'(\w)\^(\d+)', r'\1^{\2}', text)
        
        # 2. 偵測數學片段並封裝：
        # 簡單邏輯：如果整段話沒有 $，但看起來像數學題，就試著處理
        if "$" not in text:
            # 這裡我們針對您提供的範例進行特製化處理
            # 尋找從括號開始到括號結束的片段
            text = re.sub(r'(\(.*\).*)', r'$\1$', text)
        
        return text

    def _inject_healer_tags(self, code, raw_code, ops_name):
        """ 在代碼中標註修復痕跡 """
        annotated_lines = []
        for line in code.split('\n'):
            new_line = line
            # AST Fix標註: 參數處理
            if "def generate(level=1" in line and "def generate():" in raw_code:
                new_line += "  # [AST Fix: 自動補齊必全參數]"
            # AST Fix標註: 防護
            elif "question_text =" in line and "question_text" not in raw_code[:300] and "question_text = " not in raw_code[:300]:
                new_line += "  # [AST Fix: 安全初始化防護]"
            # Regex Fix 標註
            elif f"{ops_name}.format_latex(" in line and ".format(" in raw_code:
                new_line += f"  # [Regex Fix: 修正 {ops_name} API]"
            
            annotated_lines.append(new_line)
        return '\n'.join(annotated_lines)

    def _execute_code(self, code, level):
        """
        動態執行 Python 代碼並獲取結果。
        """
        # [V2.5 Unification] 優先從標準函式庫匯入
        try:
            from core.prompts.domain_function_library import (
                RadicalOps, IntegerOps, FractionOps, PolynomialOps, CalculusOps
            )
        except ImportError:
            # Fallback 到舊有的 Scaffold Libs
            try:
                from core.scaffold.domain_libs import RadicalOps, IntegerOps, FractionOps
            except ImportError:
                RadicalOps = IntegerOps = FractionOps = None
            PolynomialOps = CalculusOps = None
        
        Fraction = importlib.import_module("fractions").Fraction
        
        # [Fallback Polyfill] 為了壓制 AI 發瘋硬要呼叫 safe_eval 的幻覺，並且處理 LaTeX 語法
        def _safe_eval_polyfill(expr):
            try:
                import re
                # 替換常見的全形或人類可讀符號，並清除 LaTeX (如 \left, \right)
                s = str(expr).replace('×', '*').replace('÷', '/').replace('＋', '+').replace('－', '-')
                s = s.replace('\\times', '*').replace('\\div', '/').replace('\\cdot', '*')
                s = s.replace('\\left', '').replace('\\right', '')
                # 將 \frac{a}{b} 或 \frac(a)(b) 轉回 (a)/(b)
                s = s.replace('\\{', '(').replace('\\}', ')').replace('{', '(').replace('}', ')')
                s = re.sub(r'\\frac\(([^)]+)\)\(([^)]+)\)', r'((\1)/(\2))', s)
                
                # 放棄危險正則表達式，直接 eval (讓它變回原始狀態)
                return eval(s, {"__builtins__": {}}, {"Fraction": Fraction, "abs": abs})
            except Exception as e:
                raise Exception(f"safe_eval 計算失敗 ({expr}): 轉換後為 '{s}', 錯誤: {e}")
                
        exec_globals = {
            "random": importlib.import_module("random"),
            "math": importlib.import_module("math"),
            "Fraction": Fraction,
            "safe_eval": _safe_eval_polyfill,  # [Polyfill 植入]
            "eval": _safe_eval_polyfill,       # 連 eval 一起壓制
            "RadicalOps": RadicalOps,
            "PolynomialOps": PolynomialOps,
            "FractionOps": FractionOps,
            "IntegerOps": IntegerOps,
            "CalculusOps": CalculusOps,
            "MixedNumbers": FractionOps, # Alias for compatibility
            "Integers": IntegerOps,      # Alias for compatibility
            "format_latex": IntegerOps.fmt_num if IntegerOps else str,  # [Polyfill 植入]
            "fmt_num": IntegerOps.fmt_num if IntegerOps else str,       # [Polyfill 植入]
            "rand_nz": IntegerOps.rand_nz if IntegerOps else None,      # [Polyfill 植入]
            # [防護牆] 預設變數，防止 UnboundLocalError
            "question_text": "題目生成失敗", # 預設值
            "correct_answer": "0"            # 預設值
        }
        
        try:
            loc = {}
            # 執行代碼定義函式
            exec(code, exec_globals, loc)
            
            gen_func = loc.get("generate")
            if not gen_func:
                raise Exception("生成的代碼中找不到 generate 函式")
                
            # [動態參數檢查]
            import inspect
            sig = inspect.signature(gen_func)
            
            # 如果 AI 產出的函式不吃參數，我們就直接呼叫
            if not sig.parameters:
                result = gen_func()
            else:
                result = gen_func(level=level)
                
            return result
        except Exception as e:
            print(f"❌ 執行生成的程式碼時出錯: {e}")
            raise e

    def generate_batch(self, skill_name, input_text, n=100, batch_size=5, ablation_mode=False):
        """
        新增批量模式 (直接用 Python 迴圈高速產出 100 題)
        """
        print(f"🔄 正在為 {skill_name} 生產 {n} 題 (單次 AI 呼叫 + Python 高速迴圈)...")
        # 直接呼叫一次 custom_problems，要求他回傳 n 題，這也是在本地 Python 環境中跑 n 次 generate()
        batches = self.generate_custom_problems(skill_name, input_text, count=n, model_id='qwen3-8b', ablation_mode=ablation_mode)
        return batches

if __name__ == "__main__":
    # 簡單測試
    scaler = AdaptiveScaler()
    skill = "jh_數學2上_FourArithmeticOperationsOfPolynomial"
    for lv in [1, 2, 3]:
        print(f"\n--- 測試難度 {lv} ---")
        try:
            res = scaler.generate_problem(skill, level=lv)
            print(f"Q: {res.get('question_text')}")
            print(f"A: {res.get('correct_answer')}")
        except Exception as e:
            print(f"錯誤: {e}")
