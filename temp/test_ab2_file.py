# -*- coding: utf-8 -*-
"""測試 Ab2 文件生成功能"""

import sys
import os
sys.path.insert(0, '.')

def test_ab2_file():
    print("="*60)
    print("🧪 測試 Ab2 文件生成")
    print("="*60)
    
    # 導入文件
    try:
        sys.path.insert(0, 'skills')
        import gh_ApplicationsOfDerivatives_14b_Ab2 as skill
        
        print("✅ 文件載入成功")
        
        # 測試生成 5 次
        success_count = 0
        for i in range(5):
            try:
                result = skill.generate(level=1)
                print(f"\n第 {i+1} 題:")
                print(f"問題: {result['question_text'][:100]}...")
                print(f"答案: {result['correct_answer']}")
                success_count += 1
            except Exception as e:
                print(f"\n第 {i+1} 題失敗:")
                print(f"錯誤: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        print(f"\n成功率: {success_count}/5")
        
    except Exception as e:
        print(f"\n❌ 載入失敗: {type(e).__name__}")
        print(f"詳情: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ab2_file()
