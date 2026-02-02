"""
修復 MASTER_SPEC 中關於 derivative_results 解包順序的說明
"""
import sys
sys.path.insert(0, '.')

from app import app
from models import db, SkillGenCodePrompt

with app.app_context():
    # 讀取 MASTER_SPEC (ID 199 才是正確的)
    spec = SkillGenCodePrompt.query.get(199)
    
    if not spec:
        print("❌ 找不到 MASTER_SPEC (ID 199)")
        exit(1)
    
    print(f"✅ 找到 MASTER_SPEC (ID: {spec.id}, Skill: {spec.skill_id})")
    print(f"📝 當前長度: {len(spec.prompt_content)} 字符")
    
    # 找到 formatting 部分
    content = spec.prompt_content
    
    # 簡單替換關鍵部分
    if "格式化導數符號**：" in content:
        # 替換標題
        content = content.replace(
            "**格式化導數符號**：",
            "**格式化導數符號** ⚠️ **關鍵步驟**："
        )
        print("✅ 更新「格式化導數符號」標題")
    
    # 在「格式化導數符號」後面插入警告
    target = "對於 `derivative_orders_list` 中的每個要求的導數階數 `k`："
    if target in content:
        new_section = """⚠️ **數據結構說明**: 假設你已經生成了 `derivative_results = [(order1, deriv_terms1), (order2, deriv_terms2), ...]`
           - ⚠️ **解包順序**: 每個元素是 `(order, deriv_terms)`，**order 在前，deriv_terms 在後**
           - **✅ 正確寫法**: `for order, _ in derivative_results`
           - **❌ 錯誤寫法**: `for _, order in derivative_results` (會把 deriv_terms 列表當作 order 整數！)
           - 對於 `derivative_orders_list` 中的每個要求的導數階數 `k`："""
        content = content.replace(
            f"- {target}",
            f"- {new_section}"
        )
        print("✅ 插入解包順序警告")
    
    # 移除舊的範例行
    old_example = '           - 範例: `\' 與 \'.join(f"${_deriv_symbol_latex(order)}$" for order in orders)`'
    if old_example in content:
        content = content.replace(old_example, "")
        print("✅ 移除舊範例")

    
    # 保存修改
    spec.prompt_content = content
    db.session.commit()
    
    print("\n" + "="*60)
    print("✅ MASTER_SPEC 已更新")
    print(f"📝 新長度: {len(content)} 字符")
    print("="*60)
    
    print("\n【修改摘要】:")
    print("1. ✅ 明確說明 derivative_results 數據結構: [(order, deriv_terms), ...]")
    print("2. ✅ 強調解包順序: for order, _ in derivative_results")
    print("3. ✅ 加入錯誤示範: for _, order 會導致錯誤")
    print("4. ✅ 保持原有的 clean_latex_output 禁令")
    
    print("\n💡 下次重新生成時，AI 應該能正確處理解包順序")
