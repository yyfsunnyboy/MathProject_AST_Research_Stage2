"""修正資料庫中 ApplicationsOfDerivatives 的 MASTER_SPEC answer_display 部分"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, SkillGenCodePrompt
from app import app

app.app_context().push()

# 讀取當前的 MASTER_SPEC
prompt_obj = SkillGenCodePrompt.query.filter_by(
    skill_id='gh_ApplicationsOfDerivatives',
    prompt_type='MASTER_SPEC'
).order_by(SkillGenCodePrompt.created_at.desc()).first()

if not prompt_obj:
    print("❌ 找不到 ApplicationsOfDerivatives 的 MASTER_SPEC")
    sys.exit(1)

old_spec = prompt_obj.prompt_content

# 舊的 answer_display 部分（包含 f'(x) = 前綴）
old_answer_display = """      answer_display: |
        答案格式化規則：
        1. 對於每個請求的導數，使用 `format_polynomial_text(coefficients, degree)` (見 `cross_domain_tools`)
           這個函數會接收係數列表和最高次數，並返回一個格式化的純文本多項式字串，例如 "4x^3 - 6x^2 + 5"。
        2. 將每個導數的結果以 "f'(x) = [結果]" 的形式呈現，並用換行符分隔。
        
        **範例**：
        `ans_parts = []`
        `ans_parts.append(f"f'(x) = {format_polynomial_text(f_prime_coeffs, f_prime_degree)}")`
        `ans_parts.append(f"f'''(x) = {format_polynomial_text(f_triple_prime_coeffs, f_triple_prime_degree)}")`
        `answer = "\\n".join(ans_parts)`
        # 最終輸出：
        # f'(x) = 4x^3 - 6x^2 + 5
        # f'''(x) = 24x - 12"""

# 新的 answer_display 部分（純多項式，逗號間隔）
new_answer_display = """      answer_display: |
        答案格式化規則：
        1. 對於每個請求的導數，使用 `format_polynomial_text(coefficients, degree)` (見 `cross_domain_tools`)
           這個函數會接收係數列表和最高次數，並返回一個格式化的純文本多項式字串，例如 "4x^3 - 6x^2 + 5"。
        2. 將每個導數的結果直接顯示為純多項式，用逗號間隔，**不要包含 f'(x) = 前綴**。
        
        **範例**：
        `ans_parts = []`
        `for order, deriv_terms in derivative_results:`
        `    ans_parts.append(format_polynomial_text(deriv_coeffs, deriv_degree))`
        `answer = ", ".join(ans_parts)`
        # 最終輸出（純多項式，逗號間隔）：
        # "4x^3 - 6x^2 + 5, 24x - 12"
        
        ⚠️ 重要：此格式與前述「導數題型特殊規範」一致，確保答案不含符號前綴或等號。"""

# 替換
new_spec = old_spec.replace(old_answer_display, new_answer_display)

if new_spec == old_spec:
    print("⚠️ 警告：未找到需要替換的 answer_display 部分")
    print("   可能已經被修改過，或格式不完全匹配")
else:
    # 更新資料庫
    prompt_obj.prompt_content = new_spec
    db.session.commit()
    print("✅ 成功修正 MASTER_SPEC 的 answer_display 部分")
    print(f"   修改字數差異: {len(new_spec) - len(old_spec)} 字元")
    print()
    print("【修改摘要】")
    print("  舊格式: f'(x) = 4x^3 - 6x^2 + 5\\nf'''(x) = 24x - 12")
    print("  新格式: 4x^3 - 6x^2 + 5, 24x - 12")
    print()
    print("  現在 MASTER_SPEC 與 UNIVERSAL_GEN_CODE_PROMPT 的導數答案格式規範完全一致！")
