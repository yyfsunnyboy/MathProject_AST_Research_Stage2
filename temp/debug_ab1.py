#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""詳細測試 Ab1 錯誤"""
import sys
import traceback
sys.path.insert(0, '.')

try:
    from skills.gh_ApplicationsOfDerivatives_14b_Ab1 import generate
    q = generate()
    print('✅ Ab1 執行成功')
    print('返回類型:', type(q))
    print('返回鍵值:', list(q.keys()) if isinstance(q, dict) else 'Not a dict')
    print('完整內容:', q)
except Exception as e:
    print('❌ Ab1 執行失敗')
    print('錯誤類型:', type(e).__name__)
    print('錯誤訊息:', str(e))
    print('\n完整堆疊:')
    traceback.print_exc()
