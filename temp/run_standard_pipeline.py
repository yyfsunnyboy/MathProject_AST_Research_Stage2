#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自動化腳本：執行 sync_skills_files.py 的標準流程
選擇 gh_ApplicationsOfDerivatives，Mode 4 (Full Pipeline)，Ablation ID 3
"""

import subprocess
import sys
import os

def run_sync_with_inputs():
    """使用自動化輸入執行 sync_skills_files.py"""
    
    # 準備輸入序列：
    # 0. 課綱選擇 -> [0] ALL（全部）
    # 1. 年級選擇 -> [0] ALL
    # 2. 冊別選擇 -> [0] ALL
    # 3. 章節選擇 -> [0] ALL
    # 4. 技能選擇 -> 直接按 Enter（0 = ALL）
    # 5. 模式選擇 -> 4 (Full Pipeline)
    # 6. Ablation 選擇 -> 3 (Full Healing)
    # 7. Model Size -> 2 (14B)
    # 8. 確認 -> y
    
    inputs = [
        "0\n",      # 課綱：ALL
        "0\n",      # 年級：ALL
        "0\n",      # 冊別：ALL
        "0\n",      # 章節：ALL
        "0\n",      # 技能：ALL
        "4\n",      # Mode 4: Full Pipeline
        "3\n",      # Ablation ID 3: Full Healing
        "2\n",      # Model Size: 14B
        "y\n"       # 確認：yes
    ]
    
    input_str = "".join(inputs)
    
    print("=" * 70)
    print("🚀 啟動標準流程：sync_skills_files.py")
    print("=" * 70)
    print("\n【自動化輸入】")
    print("  課綱：ALL（全部）")
    print("  年級：ALL（全部）")
    print("  冊別：ALL（全部）")
    print("  章節：ALL（全部）")
    print("  技能：ALL（全部，包含 gh_ApplicationsOfDerivatives）")
    print("  模式：4 (Full Pipeline + AST Healing)")
    print("  Ablation：3 (Full Healing)")
    print("  模型量級：14B")
    print("\n")
    
    try:
        result = subprocess.run(
            [sys.executable, "scripts/sync_skills_files.py"],
            input=input_str,
            text=True,
            cwd=os.getcwd(),
            timeout=300,  # 5分鐘超時
            capture_output=True
        )
        
        # 只顯示最後的 100 行
        output_lines = result.stdout.split('\n')
        print("【執行輸出】（最後 100 行）")
        for line in output_lines[-100:]:
            print(line)
        
        if result.returncode == 0:
            print("\n" + "=" * 70)
            print("✅ 生成完成！")
            print("=" * 70)
        else:
            print("\n" + "=" * 70)
            print(f"❌ 返回碼: {result.returncode}")
            print("=" * 70)
            if result.stderr:
                print("\n【錯誤信息】")
                print(result.stderr[-500:])
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ 超時！腳本執行超過 5 分鐘")
        return False
    except Exception as e:
        print(f"❌ 執行失敗：{e}")
        return False

if __name__ == "__main__":
    success = run_sync_with_inputs()
    sys.exit(0 if success else 1)
