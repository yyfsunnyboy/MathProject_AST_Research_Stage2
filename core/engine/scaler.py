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

    def generate_custom_problems(self, skill_name, input_text, count=5):
        """
        根據輸入例題，完全模仿題型生成 count 題。
        """
        skill_path = self._get_skill_path(skill_name)
        skill_md_path = os.path.join(skill_path, "SKILL.md")
        
        if not os.path.exists(skill_md_path):
            raise FileNotFoundError(f"找不到技能定義: {skill_md_path}")

        print(f"🚀 正在為 {skill_name} 製作依照例題的出題腳本...")
        
        try:
            from core.code_generator import _call_ai, _basic_cleanup, _advanced_healer, _inject_domain_libs
            
            with open(skill_md_path, "r", encoding="utf-8") as f:
                skill_spec = f.read()

            # 特製 Prompt：載入 skill_spec 提供工具庫資訊，但用最高權重指令覆蓋難度規則！
            prompt = f"{skill_spec}\n\n" + \
                     f"==========================================================\n" + \
                     f"【最高優先級指令：精確模仿，完全忽略上面規格書的難度規則】\n" + \
                     f"==========================================================\n" + \
                     f"你的任務是「完全」依照以下例題的題型結構，寫出一個名為 `generate(level)` 的 Python 函式，回傳一份 Python 字典格式題目。\n\n" + \
                     f"[用戶輸入的目標模仿例題]：{input_text}\n\n" + \
                     f"【嚴格出題規則】\n" + \
                     f"1. **拋棄難度設定**：上方規格書寫的 EASY/NORMAL/HARD 規則全部作廢！只鎖定目標例題的結構。\n" + \
                     f"2. **結構必須 100% 相同**：\n" + \
                     f"   - 項數必須完全一樣。\n" + \
                     f"   - 每個多項式的「最高次數 (Degree)」必須完全一樣！例如純整數題就只能出純整數題。\n" + \
                     f"   - 運算符號（包含加減乘除、絕對值、中括號、小括號）的層級必須完全對照例題。\n" + \
                     f"3. **保證整數除法能整除且合法 (非常重要)**：\n" + \
                     f"   - 如果題型包含除法，那你必須在 Python 的 `while` 迴圈中，反覆隨機抽數字，直到 (1)被除數與除數「能夠完美整除 ( `% == 0` )」，且 (2)「除數絕對不可以是 0」再跳出迴圈。\n" + \
                     f"   - 絕對禁止產生算出除不盡的小數或被 Python 的 `int()` 硬切成 `0` 的爛題目！\n" + \
                     f"4. **絕對禁止前後重複**：\n" + \
                     f"   - 題目的各部份必須是用「不同」的隨機數字獨立生成的！絕對禁止產生前端和後端長得一模一樣的重複死板題目。\n" + \
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
            
            from config import Config
            model_config = Config.CODER_PRESETS.get('qwen3-8b')
            raw_code, _, _ = _call_ai(prompt, model_config=model_config)
            
            clean_code, _ = _basic_cleanup(raw_code)
            healed_code, *healer_stats = _advanced_healer(clean_code, ablation_id=3, skill_id=skill_name)
            final_code, _ = _inject_domain_libs(healed_code)
            
            print("\n=== DEBUG: GENERATED CODE ===")
            print(final_code)
            print("=============================\n")
            with open("debug_last_gen.py", "w", encoding="utf-8") as _fb:
                _fb.write(final_code)
            
            # 拿到 final_code 後，執行 count 次
            results = []
            for i in range(count):
                try:
                    res = self._execute_code(final_code, level=2) # pass dummy level
                    results.append(res)
                except Exception as e:
                    results.append({"error": f"執行第 {i+1} 題時發生錯誤: {e}"})
            return results

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
        
        exec_globals = {
            "random": importlib.import_module("random"),
            "math": importlib.import_module("math"),
            "Fraction": importlib.import_module("fractions").Fraction,
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
