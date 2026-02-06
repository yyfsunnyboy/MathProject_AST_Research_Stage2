#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

results_dir = r'experiments\results\gh_ApplicationsOfDerivatives'

# 統計檔案
files = sorted([f for f in os.listdir(results_dir) if f.endswith('.py')])

print(f"✅ 檔案統計: 共 {len(files)} 個檔案\n")

# 檢查檔案大小
print("檔案大小統計:")
for f in files[:5]:
    fpath = os.path.join(results_dir, f)
    size = os.path.getsize(fpath)
    print(f"  {f}: {size} bytes")

print(f"\n... 共 {len(files)} 個檔案")

# 讀取並檢查第一個檔案內容
test_file = os.path.join(results_dir, files[0])
with open(test_file, 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')
    print(f"\n第一個檔案 ({files[0]}):")
    print(f"  行數: {len(lines)}")
    print(f"  字符數: {len(content)}")
    print(f"  是否為空: {len(content) == 0}")
    print(f"\n內容預覽:")
    for i, line in enumerate(lines[:10], 1):
        if line:
            print(f"    {i}: {line[:80]}")
