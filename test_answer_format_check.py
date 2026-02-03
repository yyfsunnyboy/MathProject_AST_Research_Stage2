#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""檢查 Ab2/Ab3 答案格式是否正確"""

from skills.gh_ApplicationsOfDerivatives_14b_Ab2 import generate as gen_ab2
from skills.gh_ApplicationsOfDerivatives_14b_Ab3 import generate as gen_ab3

def check_format(name, gen_func):
    print(f"\n=== 測試 {name} ===")
    for i in range(3):
        result = gen_func()
        ans = result['correct_answer']
        print(f"Run {i+1}:")
        print(f"  原始: {repr(ans)}")
        
        # 檢查分隔符
        if '\n' in ans:
            parts = ans.split('\n')
            print(f"  ✅ 用換行分隔 ({len(parts)} 個答案)")
            for j, part in enumerate(parts, 1):
                print(f"     答案{j}: {part}")
        elif ' ' in ans:
            parts = ans.split(' ')
            print(f"  ⚠️ 用空格分隔 ({len(parts)} 個答案)")
            for j, part in enumerate(parts, 1):
                print(f"     答案{j}: {part}")
        else:
            print(f"  ✅ 單一答案")

check_format("Ab2", gen_ab2)
check_format("Ab3", gen_ab3)
