"""
精確修復 MASTER_SPEC - 移除 clean_latex_output 指令
"""
import sys
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
    
    # 簡單替換：移除 clean_latex_output 指令
    fixed_content = original_content.replace(
        '           - 最後呼叫 `q = clean_latex_output(q)`。',
        ('           - 🔴 **禁止**: 不要呼叫 `clean_latex_output(q)`。\n' +
         '           - 原因: derivative_symbols_latex 中的每個符號必須手動添加 $...$ 包裹。\n' +
         '           - 範例: `\' 與 \'.join(f"${_deriv_symbol_latex(order)}$" for order in orders)`')
    )
    
    if fixed_content != original_content:
        spec.prompt_content = fixed_content
        db.session.commit()
        print("\n✅ MASTER_SPEC 已更新")
        
        # 顯示修改後的內容
        lines = fixed_content.split('\n')
        print("\n【修改後的「組合題目」段落】:")
        for i, line in enumerate(lines):
            if '組合題目' in line:
                for j in range(i, min(i+8, len(lines))):
                    print(lines[j])
                break
    else:
        print("\n⚠️  內容沒有變化")
