#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script to verify gh_ApplicationsOfDerivatives_14B_Ab3 fix"""

import time
import sys

sys.path.insert(0, '.')

print('測試修復後的 generate()，嘗試 10 次生成...')
print('=' * 60)

try:
    from skills.gh_ApplicationsOfDerivatives_14B_Ab3 import generate
    
    total_time = 0
    for i in range(10):
        start = time.time()
        result = generate()
        elapsed = time.time() - start
        total_time += elapsed
        
        ans = result.get('correct_answer', 'N/A')[:20]
        print(f'[{i+1:2d}] ✅ {elapsed:.3f}s - {ans}')
        
    print('=' * 60)
    print(f'✅ 全部成功！平均耗時: {total_time/10:.3f}s')
    print(f'   總耗時: {total_time:.2f}s')
    
except Exception as e:
    elapsed = time.time() - start
    print(f'❌ 失敗！耗時 {elapsed:.2f} 秒')
    print(f'錯誤: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

