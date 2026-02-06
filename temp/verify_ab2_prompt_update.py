# -*- coding: utf-8 -*-
"""
验证 Ab2 Prompt 更新是否成功
检查所有关键优化点是否已应用到生成的 prompt 中
"""

import sys
sys.path.insert(0, '.')

from core.prompts.prompt_builder import PromptBuilder

def main():
    print("=" * 80)
    print("验证 Ab2/Ab3 Prompt 更新")
    print("=" * 80)
    print()
    
    # 生成 Ab2 prompt
    master_spec = """【题型描述】求多项式函数的导数

【复杂度要求】
- 多项式次数：3-5 次
- 系数范围：-10 到 10
- 求导次数：随机选择 2 个不同阶数

【输出格式】
- 题目使用 LaTeX 格式
- 答案为纯多项式文字"""
    
    ab2_prompt = PromptBuilder.build(
        master_spec=master_spec,
        ablation_id=2,
        skill_id='gh_ApplicationsOfDerivatives'
    )
    
    print(f"✅ Ab2 Prompt 总长度: {len(ab2_prompt)} 字符")
    print()
    
    # 检查关键优化点
    checks = {
        "步骤 2.2 - 至少 3 总项": "# 至少 3 總項 (包括最高次項)",
        "步骤 2.3 - 实际使用 shuffle": "# ✅ 實際使用 shuffle 結果！",
        "步骤 2.4 - shuffle 控制结构": "# ✅ shuffle 直接控制多項式結構！",
        "步骤 3 - terms 是 List": "# ✅ 關鍵示範：這裡產生的 terms 是List，專門給計算用的",
        "步骤 4 - 传入 List 而非字符串": "# ✅ 關鍵示範：傳入的是 terms (List)，絕對不是字串！",
        "步骤 6 - 算完才转 String": "# ✅ 關鍵示範：算完之後，才把結果轉成 String",
        "答案格式铁律": "🔴 答案格式铁律",
        "_differentiate_poly 类型说明": "🔴 注意：必须是 list，不能是字符串"
    }
    
    print("=== 关键优化点检查 ===")
    all_passed = True
    for check_name, check_pattern in checks.items():
        if check_pattern in ab2_prompt:
            print(f"✅ {check_name}")
        else:
            print(f"❌ {check_name} - 未找到")
            all_passed = False
    
    print()
    
    # 保存到文件
    import os
    os.makedirs('temp', exist_ok=True)
    with open('temp/ab2_full_prompt_verified.txt', 'w', encoding='utf-8') as f:
        f.write(ab2_prompt)
    
    print(f"✅ 已保存到: temp/ab2_full_prompt_verified.txt")
    print()
    
    if all_passed:
        print("🎉 所有关键优化点均已成功应用！")
    else:
        print("⚠️ 部分优化点未找到，请检查代码")
    
    print()
    print("=" * 80)
    print("验证完成")
    print("=" * 80)

if __name__ == '__main__':
    main()
