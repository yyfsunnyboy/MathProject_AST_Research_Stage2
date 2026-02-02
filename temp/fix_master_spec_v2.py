"""
精確修復 MASTER_SPEC - 使用正則表達式
"""
import sys
import re
sys.path.insert(0, '.')

from models import db, SkillGenCodePrompt
from app import create_app

app = create_app()

with app.app_context():
    spec = SkillGenCodePrompt.query.get(199)
    
    if not spec:
        print("❌ 找不到 MASTER_SPEC")
        sys.exit(1)
    
    print(f"✅ 找到 MASTER_SPEC (ID: {spec.id})")
    
    original_content = spec.prompt_content
    fixed_content = original_content
    
    # 修復 2 & 3: 使用正則表達式替換整個 formatting section
    pattern = r'(        2\. \*\*格式化導數符號\*\*：.*?)(        3\. \*\*組合題目\*\*：.*?最後呼叫 `q = clean_latex_output\(q\)`\.)'
    
    replacement = r'''\1        3. **組合題目**：
           - `q = f"已知 $f(x) = {poly_latex}$，求 {derivative_symbols_latex}。"`
           - 🔴 **禁止**: 不要呼叫 `clean_latex_output(q)`，因為導數符號已經包含 $ $ 符號。
           - 🔴 **關鍵**: derivative_symbols_latex 中的每個符號必須被 $...$ 包裹（如 "$f'(x)$ 與 $f'''(x)$"）。'''
    
    # 先找到並打印原始段落
    match = re.search(r'3\. \*\*組合題目\*\*：[^\n]*\n[^\n]*', fixed_content, re.DOTALL)
    if match:
        print("\n【原始的「組合題目」段落】:")
        print(match.group(0))
    
    # 簡單替換：直接替換「最後呼叫」那一行
    fixed_content = fixed_content.replace(
        '           - 最後呼叫 `q = clean_latex_output(q)`。',
        '           - 🔴 **禁止**: 不要呼叫 `clean_latex_output(q)`，因為導數符號已包含 $ $ 符號。\n' +
        '           - 🔴 **關鍵**: derivative_symbols_latex 的每個符號必須用 $...$ 包裹。\n' +
        '           - 範例: `\' 與 \'.join(f"${symbol}$" for symbol in symbols_list)`'
    )
    
    if fixed_content != original_content:
        spec.prompt_content = fixed_content
        db.session.commit()
        print("\n✅ MASTER_SPEC 已更新")
        print("\n【修改後的「組合題目」段落】:")
        match = re.search(r'3\. \*\*組合題目\*\*：[^\n]*\n[^\n]*\n[^\n]*\n[^\n]*', fixed_content, re.DOTALL)
        if match:
            print(match.group(0))
    else:
        print("\n⚠️  內容沒有變化")
