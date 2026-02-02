"""
修復 gh_ApplicationsOfDerivatives 的 MASTER_SPEC
"""
import sys
sys.path.insert(0, '.')

from models import db, SkillGenCodePrompt
from app import create_app

app = create_app()

with app.app_context():
    # 獲取當前的 MASTER_SPEC
    spec = SkillGenCodePrompt.query.filter_by(
        skill_id='gh_ApplicationsOfDerivatives',
        prompt_type='MASTER_SPEC'
    ).order_by(SkillGenCodePrompt.created_at.desc()).first()
    
    if not spec:
        print("❌ 找不到 MASTER_SPEC")
        sys.exit(1)
    
    print(f"✅ 找到 MASTER_SPEC (ID: {spec.id})")
    
    # 讀取原始內容
    original_content = spec.prompt_content
    
    # 修復 1: num_terms 邏輯
    fixed_content = original_content.replace(
        """          1. 隨機選擇最高次數 `max_degree` (3~5)。
          2. 隨機選擇非零項數 `num_terms` (3~5)。""",
        """          1. 隨機選擇最高次數 `max_degree` (3~5)。
          2. 隨機選擇非零項數 `num_terms` (3~5，但不能超過 max_degree + 1)。"""
    )
    
    # 修復 2: 移除 clean_latex_output 指令，改為手動添加 $ 符號
    fixed_content = fixed_content.replace(
        """        2. **格式化導數符號**：
           - 對於 `derivative_orders_list` 中的每個要求的導數階數 `k`：
             - 若 `k=1`，使用 `f'(x)`。
             - 若 `k=2`，使用 `f''(x)`。
             - 若 `k=3`，使用 `f'''(x)`。
             - 若 `k > 3`，使用 `f^{(k)}(x)`。
           - 將這些格式化的導數符號用「與」或逗號連接起來，例如 "$f'(x)$ 與 $f'''(x)$"。
           - 儲存為 `derivative_symbols_latex` 字串。

        3. **組合題目**：
           - `q = f"已知 $f(x) = {poly_latex}$，求 {derivative_symbols_latex}。"`
           - 最後呼叫 `q = clean_latex_output(q)`。""",
        """        2. **格式化導數符號**：
           - 對於 `derivative_orders_list` 中的每個要求的導數階數 `k`：
             - 若 `k=1`，使用 `f'(x)`。
             - 若 `k=2`，使用 `f''(x)`。
             - 若 `k=3`，使用 `f'''(x)`。
             - 若 `k > 3`，使用 `f^{(k)}(x)`。
           - 🔴 **關鍵**: 將每個符號用 `$...$` 包裹，然後用「與」連接。
           - 範例: `derivative_symbols_latex = ' 與 '.join(f"${symbol}$" for symbol in symbols_list)`
           - 最終結果如: "$f'(x)$ 與 $f'''(x)$"。
           - 儲存為 `derivative_symbols_latex` 字串。

        3. **組合題目**：
           - `q = f"已知 $f(x) = {poly_latex}$，求 {derivative_symbols_latex}。"`
           - 🔴 **禁止**: 不要呼叫 `clean_latex_output(q)`，因為 Domain 函數已經處理好 LaTeX 格式。"""
    )
    
    # 檢查是否有修改
    if fixed_content == original_content:
        print("⚠️  沒有找到需要替換的內容，請手動檢查")
        print("\n原始內容片段:")
        print(original_content[2000:2500])
    else:
        print("✅ 內容已修改")
        
        # 更新數據庫
        spec.prompt_content = fixed_content
        db.session.commit()
        
        print("✅ MASTER_SPEC 已更新到數據庫")
        print("\n修改摘要:")
        print("1. num_terms 生成規則: 添加「但不能超過 max_degree + 1」限制")
        print("2. 導數符號格式化: 明確要求為每個符號添加 $ $ 包裹")
        print("3. 組合題目: 禁止呼叫 clean_latex_output(q)")
