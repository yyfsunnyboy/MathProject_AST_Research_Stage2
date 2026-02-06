#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""驗證生成的 gh_ApplicationsOfDerivatives 檔案品質"""

import sys
import re
import time

print("=" * 70)
print("【驗證 gh_ApplicationsOfDerivatives 技能檔案】")
print("=" * 70)

test_files = [
    "gh_ApplicationsOfDerivatives",
    "gh_ApplicationsOfDerivatives_14B_Ab3"
]

for file_name in test_files:
    print(f"\n【測試：{file_name}.py】")
    print("-" * 70)
    
    try:
        # 動態導入
        module_name = file_name.replace('.py', '')
        exec(f"from skills.{module_name} import generate")
        generate = eval("generate")
        
        # 條件 1：無限迴圈檢查
        print("\n1️⃣  檢查無限迴圈...")
        loop_ok = True
        for i in range(5):
            start = time.time()
            try:
                result = generate()
                elapsed = time.time() - start
                if elapsed > 1.0:
                    print(f"   ❌ 第 {i+1} 次耗時 {elapsed:.2f}s（超過 1s，可能有無限迴圈）")
                    loop_ok = False
                    break
                else:
                    print(f"   ✅ 第 {i+1} 次耗時 {elapsed:.3f}s")
            except KeyboardInterrupt:
                print(f"   ❌ 第 {i+1} 次被中斷（無限迴圈）")
                loop_ok = False
                break
        
        if loop_ok:
            print("   ✅ 全部在 1s 內完成，無無限迴圈")
        
        # 條件 2 & 3 & 4：LaTeX、中文、答案格式
        print("\n2️⃣  檢查格式品質...")
        
        latex_ok = False
        chinese_not_in_latex_ok = True
        answer_clean_ok = True
        
        samples = []
        for i in range(3):
            result = generate()
            q = result.get('question_text', '')
            a = result.get('correct_answer', '')
            
            samples.append({
                'q': q,
                'a': a,
                'has_latex_q': '$' in q,
                'has_latex_a': '$' in a or '\\' in a,
                'has_chinese_q': bool(re.search(r'[\u4e00-\u9fff]', q))
            })
        
        # 2. LaTeX 語法檢查
        if any(s['has_latex_q'] for s in samples):
            print("   ✅ 題目包含 LaTeX 語法")
            latex_ok = True
        else:
            print("   ❌ 題目沒有 LaTeX 語法")
        
        # 3. 中文不在 LaTeX 裡面
        latex_blocks = re.findall(r'\$([^$]*)\$', ''.join(s['q'] for s in samples))
        for block in latex_blocks:
            if re.search(r'[\u4e00-\u9fff]', block):
                print(f"   ❌ 發現中文在 LaTeX 裡: {block[:50]}")
                chinese_not_in_latex_ok = False
                break
        
        if chinese_not_in_latex_ok:
            print("   ✅ 中文沒有被包在 LaTeX 裡面")
        
        # 4. 答案乾淨
        for i, s in enumerate(samples):
            if s['has_latex_a']:
                print(f"   ❌ 第 {i+1} 個答案包含 LaTeX: {s['a'][:50]}")
                answer_clean_ok = False
            else:
                print(f"   ✅ 第 {i+1} 個答案乾淨: {s['a'][:50]}")
        
        # 總結
        print("\n【驗證結果】")
        results = {
            '1. 無限迴圈': '✅ 通過' if loop_ok else '❌ 失敗',
            '2. LaTeX 語法': '✅ 通過' if latex_ok else '❌ 失敗',
            '3. 中文不在 LaTeX': '✅ 通過' if chinese_not_in_latex_ok else '❌ 失敗',
            '4. 答案乾淨': '✅ 通過' if answer_clean_ok else '❌ 失敗'
        }
        
        all_pass = all('✅' in v for v in results.values())
        
        for item, status in results.items():
            print(f"   {item}: {status}")
        
        if all_pass:
            print(f"\n🎉 {file_name} 全部驗證通過！")
        else:
            print(f"\n⚠️  {file_name} 有問題需要修復")
        
    except ModuleNotFoundError as e:
        print(f"❌ 找不到模組: {e}")
    except Exception as e:
        print(f"❌ 執行失敗: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print("驗證完成！")
print("=" * 70)
