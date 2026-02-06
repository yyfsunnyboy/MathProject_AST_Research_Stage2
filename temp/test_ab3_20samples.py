#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test Ab3 with 20 samples to simulate research_runner load"""

import time
import sys

sys.path.insert(0, '.')

print('採樣 gh_ApplicationsOfDerivatives_14B_Ab3 的 20 個題目...')
print('=' * 60)

try:
    from skills.gh_ApplicationsOfDerivatives_14B_Ab3 import generate
    
    start = time.time()
    for i in range(20):
        result = generate()
        print(f'[{i+1:2d}] ✅')
        if (i + 1) % 5 == 0:
            elapsed_so_far = time.time() - start
            print(f'    進度: {i+1}/20, 耗時 {elapsed_so_far:.2f}s')
    
    elapsed = time.time() - start
    print('=' * 60)
    print(f'✅ 全部完成！')
    print(f'   總耗時: {elapsed:.2f} 秒')
    print(f'   平均: {elapsed/20*1000:.1f}ms/題')
    
except KeyboardInterrupt:
    elapsed = time.time() - start
    print(f'\n❌ 被中斷！耗時 {elapsed:.2f} 秒')
    print('   可能是卡在無限迴圈')
    sys.exit(1)
except Exception as e:
    elapsed = time.time() - start
    print(f'\n❌ 失敗！耗時 {elapsed:.2f} 秒')
    print(f'   錯誤: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
