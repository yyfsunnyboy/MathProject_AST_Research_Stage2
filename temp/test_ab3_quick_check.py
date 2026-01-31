#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速驗證 Ab3 生成（測試新的 remove_system_overrides）
確保 IndentationError 已被修復
"""

import sys
import subprocess
from pathlib import Path

def test_ab3_generation():
    """測試單一技能的 Ab3 生成"""
    
    print("=" * 70)
    print("🧪 Ab3 生成快速驗證（整塊移除版本）")
    print("=" * 70)
    
    skill_id = "gh_ApplicationsOfDerivatives"
    
    print(f"\n📌 測試技能: {skill_id}")
    print(f"🎯 目標: 驗證 Ab3 生成不出現 IndentationError")
    print(f"🔧 關鍵修復: remove_system_overrides 整塊移除版本\n")
    
    # 檢查必要文件
    print("📂 檢查環境...")
    required_files = [
        Path("core/code_generator.py"),
        Path("instance/kumon_math.db"),
        Path("core/code_utils/math_utils.py"),
    ]
    
    for f in required_files:
        if f.exists():
            print(f"  ✅ {f}")
        else:
            print(f"  ❌ 缺失 {f}")
            return False
    
    print("\n🚀 執行 Ab3 生成...")
    print("-" * 70)
    
    # 執行生成命令
    cmd = [
        sys.executable,
        "scripts/quick_validate_highschool.py",
        "--skill", skill_id,
        "--ablation", "3"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # 檢查結果
        print("-" * 70)
        
        if result.returncode == 0:
            print("\n✅ 生成成功！")
            
            # 檢查是否有 IndentationError
            if "IndentationError" in result.stdout or "IndentationError" in result.stderr:
                print("❌ 警告：仍然存在 IndentationError")
                return False
            
            # 檢查是否有 Success 標記
            if "Success" in result.stdout or "成功" in result.stdout:
                print("✅ 驗證通過 - 無 IndentationError")
                
                # 檢查是否生成了檔案
                skill_file = Path(f"skills/{skill_id}_Cloud_Ab3.py")
                if skill_file.exists():
                    print(f"✅ 技能檔案已生成: {skill_file}")
                    
                    # 檢查檔案內容
                    with open(skill_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 檢查是否移除了系統函式
                    if "def fmt_num(" not in content:
                        print("✅ 系統函式已移除（def fmt_num 不存在）")
                    else:
                        print("⚠️  警告：def fmt_num 仍存在（可能是正常定義）")
                    
                    # 檢查是否有孤立的縮排
                    lines = content.split('\n')
                    orphaned_indents = []
                    for i, line in enumerate(lines, 1):
                        if line and line[0] in (' ', '\t') and i > 1:
                            prev_line = lines[i-2].strip()
                            if not prev_line or prev_line.startswith('#'):
                                orphaned_indents.append(i)
                    
                    if not orphaned_indents:
                        print("✅ 無孤立的縮排行")
                    else:
                        print(f"⚠️  檢測到孤立的縮排行: {orphaned_indents}")
                        return False
                    
                    return True
                else:
                    print(f"❌ 技能檔案未生成: {skill_file}")
                    return False
            else:
                print("⚠️  生成結果不確定")
                return False
        else:
            print(f"\n❌ 生成失敗（返回碼 {result.returncode}）")
            return False
            
    except subprocess.TimeoutExpired:
        print("\n❌ 生成超時（120秒）")
        return False
    except Exception as e:
        print(f"\n❌ 執行錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_ab3_generation()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 Ab3 生成驗證成功！")
        print("🔧 remove_system_overrides 整塊移除版本正常運作")
        print("=" * 70)
        sys.exit(0)
    else:
        print("❌ Ab3 生成驗證失敗")
        print("=" * 70)
        sys.exit(1)
