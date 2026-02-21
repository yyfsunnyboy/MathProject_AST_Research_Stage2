# -*- coding: utf-8 -*-
import os
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
        try:
            from core.code_generator import _call_ai, _basic_cleanup, _advanced_healer, _inject_domain_libs
            
            if ablation_mode:
                # [Ab1 裸奔模式]：跳過 SKILL.md，給予最精簡的原生 Prompt
                print(f"⚠️ 警告：已開啟 Ab1 消融模式，跳過 {skill_name} 的 Scaffold Prompt 與 Healer 自癒機制。")
                prompt = f"請寫一個名為 `generate(level=1)` 的 Python 函式，回傳包含題目的字典。\n" + \
                         f"字典格式必須要有 `question_text` 與 `correct_answer`。\n" + \
                         f"請參考以下例題的風格隨機出題：\n{input_text}\n" + \
                         f"直接印出含 generate(level) 的 Python 程式碼，不需解釋。"
                active_ablation_id = 1
            else:
                # [Ab3 神盾模式]：載入完整的知識庫與防護網
                print(f"🚀 正在為 {skill_name} 製作依照例題的出題腳本...")
                skill_path = self._get_skill_path(skill_name)
                skill_md_path = os.path.join(skill_path, "SKILL.md")
                if not os.path.exists(skill_md_path):
                    raise FileNotFoundError(f"找不到技能定義: {skill_md_path}")
                with open(skill_md_path, "r", encoding="utf-8") as f:
                    skill_spec = f.read()

                # 特製 Prompt：載入 skill_spec 提供工具庫資訊，並加上 LaTeX 與安全防護規則
                prompt = f"{skill_spec}\n\n" + \
                         f"==========================================================\n" + \
                         f"【動態出題腳本實作需求】\n" + \
                         f"==========================================================\n" + \
                         f"你的任務是根據上方規格書，參考以下例題的風格，寫出一個名為 `generate(level=1)` 的 Python 函式，回傳字典格式題目。\n\n" + \
                         f"[目標模仿例題]：{input_text}\n\n" + \
                         f"【出題規則與安全限制】\n" + \
                         f"1. **難度與變化**：請遵循規格書對 EASY/NORMAL/HARD (Level 1/2/3) 的定義。你可以使用 random 模組在結構中加入安全的隨機變化。\n" + \
                         f"2. **保證運算合法且避免崩潰 (非常重要)**：\n" + \
                         f"   - **絕對禁止分母為 0**：如果你的演算法需要生成分數 (Fraction) 或除法，請用 `while` 迴圈不斷隨機抽籤，直到分母 / 除數「不等於 0」為止，否則會發生 `Fraction(x, 0)` 或 `ZeroDivisionError` 當機！\n" + \
                         f"   - **禁止括號計算出 0 作為除數**：如果你生成了像 `(a - b)` 這樣的括號，且它位於除號或分數的下方，你必須在迴圈中檢查 `a != b`，絕對不可以出現 `(3 - 3)` 這種導致除以零的無效數學題！\n" + \
                         f"   - **整數除法合法**：反覆隨機抽數字，直到 (1)能完美整除且 (2)除數絕對不為 0。絕對禁止產生小數或被 `int()` 硬切。\n" + \
                         f"   - **禁止小數直接呼叫分母**：絕對不可以對小數 (float) 屬性呼叫 `.denominator` 或 `.numerator`！若有小數請轉換為 `Fraction(15, 10)` 等形式再操作。\n" + \
                         f"   - **絕對禁止使用 eval() 或 safe_eval()**：系統環境內沒有 `safe_eval`！絕對禁止將方程式組成字串再來計算！你必須**先用 Python 變數實體算出結果** (例如 `ans = frac1 + frac2`)，再把 `ans` 轉換成字串當作對答案。\n" + \
                         f"   - **變數定義必須完整**：確保你程式碼中使用的所有變數（如 `val3`、`frac1`）在操作前都已經明確定義，避免發生 `NameError`。\n" + \
                         f"   - **嚴格遵守 LaTeX 格式**：輸出的 `question_text` 數學式部分必須是標準的 LaTeX。請使用 `\\times` 代替 `×` 或 `*`，用 `\\div` 代替 `÷` 或 `/`。分數用 `\\frac{{a}}{{b}}`。數學式最外層請用單一的 `$` 包裹（例如：`計算 $(-3) + 5$ 的值`），絕對不要前後加一堆空白或使用 `$$`。\n" + \
                         f"   - **純淨的數學字串**：你在運算 `expr` 的時候，裡面只能有數字和數學符號，絕對不能包含「計算 ... 的值」這種中文！中文只能加在最後的 `question_text` 的字串前綴中。\n" + \
                         f"5. **強制使用官方包裹函式與字串格式化 (預防 NameError 與語法錯亂)**：\n" + \
                         f"   - 絕對不可以直接呼叫 `fmt_num(...)` 或 `to_latex(...)`！這會造成 Crash！\n" + \
                         f"   - 若要格式化整數，必須寫成 `IntegerOps.fmt_num(...)`。\n" + \
                         f"   - 若要格式化分數，**請直接使用 Python 字串 f-string：`f\"\\frac{{frac.numerator}}{{frac.denominator}}\"`**，或者使用 `FractionOps.to_latex(frac)`，絕對不可使用其他不存在的函式。\n" + \
                         f"   - 若為根式(根號)題型，請務必使用 `RadicalOps.format_term(coeff, radicand, is_first)` 或 `format_term_unsimplified` 進行標準格式化。\n" + \
                         f"   - ⚠️ 【極度重要！避免加減號重複】：如果你的題目樣板字串中已經自帶了括號或加減號（例如 `f\"({{term1}}) - {{term2}}\"`），那麼在格式化 `term1` 與 `term2` 時，**「必須」將它們的 `is_first` 參數全部設為 `True`！** 否則 `is_first=False` 會自動產生一個帶有 `+` 號的字串，導致最後變成 `( + 3\\sqrt{2} ) -  + 5\\sqrt{5}` 這種含有致命重複符號的爛題目！\n" + \
                         f"6. 你的 generate() 函式內部「必須」使用 random 模組隨機決定數字或符號，保證每次呼叫 generate() 都會產生全新的組合。\n" + \
                         f"7. 若例題中根號內部包分數（例如 `\\sqrt{{\\frac{{1}}{{3}}}}`），請在輸出字串時靈活使用 f-string 自行排版，並於後端正確計算。\n" + \
                         f"8. 請正確計算出對應的答案。回傳的字典必須包含 `question_text` 與 `correct_answer`。\n" + \
                         f"請直接輸出含有 `generate(level)` 定義的 Python 程式碼，不需要任何額外的說明。"
                active_ablation_id = 3
            
            import time
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
                final_code, _ = _inject_domain_libs(healed_code)
                regex_fixes = healer_stats[0] if len(healer_stats) > 0 else 0
                ast_fixes = healer_stats[1] if len(healer_stats) > 1 else 0
            
            print("\n=== DEBUG: GENERATED CODE ===")
            print(final_code)
            print("=============================\n")
            with open("debug_last_gen.py", "w", encoding="utf-8") as _fb:
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
                    res = self._execute_code(final_code, level=2) # pass dummy level
                    
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
                "raw_code": raw_code,
                "thinking": thinking_text,
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
            "Integers": IntegerOps       # Alias for compatibility
        }
        
        try:
            # 執行代碼定義函式
            exec(code, exec_globals)
            
            if "generate" not in exec_globals:
                raise Exception("生成的代碼中找不到 generate 函式")
                
            # 呼叫 generate(level)
            result = exec_globals["generate"](level=level)
            return result
        except Exception as e:
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
