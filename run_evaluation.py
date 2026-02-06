#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""運行完整評分流程"""
import subprocess
import sys

print("\n" + "="*80)
print("🚀 開始評分流程...")
print("="*80 + "\n")

proc = subprocess.Popen(
    [sys.executable, 'scripts/evaluate_mcri.py'],
    stdin=subprocess.PIPE,
    text=True,
    encoding='utf-8',
    errors='replace'
)

try:
    # 提供 'y' 確認開始評分
    proc.communicate(input='y\n', timeout=600)
except subprocess.TimeoutExpired:
    proc.kill()
    print("\n❌ 進程超時（600秒）")
    sys.exit(1)
except KeyboardInterrupt:
    proc.kill()
    print("\n⏹️  使用者中斷")
    sys.exit(1)

sys.exit(proc.returncode)
