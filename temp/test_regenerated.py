#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""全面測試三個 Ab 檔案"""
import sys
import traceback
sys.path.insert(0, '.')

results = []
for variant in ['Ab1', 'Ab2', 'Ab3']:
    try:
        mod = __import__(f'skills.gh_ApplicationsOfDerivatives_14b_{variant}', fromlist=['generate'])
        q = mod.generate()
        
        # 檢查返回值結構
        if not isinstance(q, dict):
            results.append((variant, '❌ 失敗', f'返回值不是 dict: {type(q)}'))
            continue
            
        if 'question_text' not in q or 'correct_answer' not in q:
            results.append((variant, '❌ 失敗', f'缺少必要鍵: {list(q.keys())}'))
            continue
        
        # 檢查答案格式
        ans = q['correct_answer']
        if variant == 'Ab1':
            ans_type = f'dict ({len(ans)} keys)' if isinstance(ans, dict) else f'str (len={len(ans)})'
        else:
            ans_type = 'str' if isinstance(ans, str) else f'{type(ans).__name__}'
        
        # 檢查答案內容
        ans_preview = str(ans)[:50] if len(str(ans)) > 50 else str(ans)
        
        results.append((variant, '✅ 成功', f'{ans_type} | {ans_preview}...'))
        
    except Exception as e:
        error_msg = f'{type(e).__name__}: {str(e)[:40]}'
        results.append((variant, '❌ 失敗', error_msg))

print('\n' + '='*100)
print('重新生成檔案測試結果')
print('='*100)
for variant, status, info in results:
    print(f'{variant:4s} | {status:10s} | {info}')
print('='*100)
