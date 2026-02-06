#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from skills.jh_數學1上_FourArithmeticOperationsOfIntegers_14b_Ab3 import generate

print("測試 Ab3.py 代碼生成...")
for i in range(3):
    try:
        q = generate()
        print(f"✅ 生成 {i+1}: {q['question_text'][:60]}...")
        print(f"   答案: {q['correct_answer']}")
    except Exception as e:
        print(f"❌ 生成 {i+1} 失敗: {e}")
        import traceback
        traceback.print_exc()
        break
