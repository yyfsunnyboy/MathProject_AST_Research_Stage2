#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""測試完整評分流程（快速版）"""
import subprocess
import sys

print("開始評分流程測試...")
print("="*80)

# 用 subprocess 提供輸入
proc = subprocess.Popen(
    [sys.executable, 'scripts/evaluate_mcri.py'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding='utf-8',
    errors='replace'
)

try:
    # 提供輸入並等待完成（最多 300 秒）
    output, _ = proc.communicate(input='y\n', timeout=300)
    print(output)
except subprocess.TimeoutExpired:
    proc.kill()
    print("❌ 進程超時")
    sys.exit(1)
except Exception as e:
    proc.kill()
    print(f"❌ 異常: {e}")
    sys.exit(1)

if proc.returncode == 0:
    print("\n✅ 評分完成成功")
else:
    print(f"\n❌ 評分失敗 (退出碼: {proc.returncode})")
    sys.exit(1)
