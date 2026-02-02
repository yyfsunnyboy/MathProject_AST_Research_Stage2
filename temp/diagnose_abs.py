#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""診斷三個檔案的具體問題"""
import sys
import traceback
sys.path.insert(0, '.')

for variant in ['Ab1', 'Ab2', 'Ab3']:
    print(f"\n{'='*60}")
    print(f"測試 {variant}")
    print('='*60)
    try:
        mod = __import__(f'skills.gh_ApplicationsOfDerivatives_14b_{variant}', fromlist=['generate'])
        for i in range(3):
            try:
                q = mod.generate()
                print(f"✅ 生成 {i+1}: 成功")
                print(f"   題目: {q['question_text'][:60]}...")
                print(f"   答案類型: {type(q['correct_answer']).__name__}")
                print(f"   答案: {str(q['correct_answer'])[:80]}...")
                break
            except Exception as e:
                print(f"❌ 生成 {i+1}: {type(e).__name__}: {str(e)[:60]}")
                if i == 2:
                    traceback.print_exc()
    except Exception as e:
        print(f"❌ 載入失敗: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
