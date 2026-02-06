#!/usr/bin/env python3
"""
實驗：高中 vs 國中技能的生成成功率對比

測試設計：
- 高中：3-5 個技能（複雜度各異）
- 國中：3-5 個技能（複雜度各異）
- 各技能生成 5 次
- 記錄：成功/失敗、修復情況

目的：判斷是否高中簡單題天花板效應明顯，還是有修復空間
"""

import os
import sys
import json
import time
import random
from pathlib import Path
from datetime import datetime

# 需要的技能清單
SKILLS_TO_TEST = {
    "高中_複雜度3": {
        "file": "skills/backup_GenByGemini/gh_PolynomialInequalities.py",
        "category": "高中",
        "complexity": 3,
        "lines": 931
    },
    "高中_複雜度2a": {
        "file": "skills/backup_GenByGemini/gh_ApplicationsOfDerivatives.py",
        "category": "高中",
        "complexity": 2,
        "lines": 758
    },
    "高中_複雜度2b": {
        "file": "skills/backup_GenByGemini/gh_RealExponentsAndLaws.py",
        "category": "高中",
        "complexity": 2,
        "lines": 714
    },
    "高中_複雜度1": {
        "file": "skills/backup_GenByGemini/gh_GeometricMeaningOfLinearEquations.py",
        "category": "高中",
        "complexity": 1,
        "lines": 497
    },
    "國中_複雜度3a": {
        "file": "skills/backup_20260129/jh_數學2下_FunctionGraph.py",
        "category": "國中",
        "complexity": 3,
        "lines": 794
    },
    "國中_複雜度3b": {
        "file": "skills/backup_20260129/jh_數學2上_FourOperationsOfRadicals.py",
        "category": "國中",
        "complexity": 3,
        "lines": 864
    },
    "國中_複雜度2": {
        "file": "skills/backup_20260129/jh_數學1上_IntegerAdditionOperation.py",
        "category": "國中",
        "complexity": 2,
        "lines": 425
    },
    "國中_複雜度1": {
        "file": "skills/backup_20260129/jh_數學1上_ComparingNumbers.py",
        "category": "國中",
        "complexity": 1,
        "lines": 227
    },
}

def check_skill_exists(skill_path):
    """檢查技能文件是否存在"""
    return Path(skill_path).exists()

def extract_skill_id(skill_path):
    """從文件路徑提取 skill_id"""
    return Path(skill_path).stem

def print_test_plan():
    """顯示測試計畫"""
    print("=" * 80)
    print("🧪 高中 vs 國中技能生成實驗計畫")
    print("=" * 80)
    print()
    
    print("【待測技能清單】")
    print()
    
    # 高中技能
    print("📍 高中技能（高中旺宏科學獎出題範圍）：")
    for skill_id, info in SKILLS_TO_TEST.items():
        if info["category"] == "高中":
            exists = "✅" if check_skill_exists(info["file"]) else "❌"
            print(f"  {exists} {skill_id:<15} | 複雜度{info['complexity']} | {info['lines']:>4}行 | {info['file']}")
    
    print()
    print("📍 國中技能（備選方案對比）：")
    for skill_id, info in SKILLS_TO_TEST.items():
        if info["category"] == "國中":
            exists = "✅" if check_skill_exists(info["file"]) else "❌"
            print(f"  {exists} {skill_id:<15} | 複雜度{info['complexity']} | {info['lines']:>4}行 | {info['file']}")
    
    print()
    print("【測試設計】")
    print(f"  • 每個技能生成 5 次")
    print(f"  • 共 {len(SKILLS_TO_TEST)} 個技能 × 5 次 = {len(SKILLS_TO_TEST) * 5} 個測試點")
    print(f"  • 測量指標：成功率 / 修復率 / 代碼品質")
    print()
    print("【預期發現】")
    print("  • 高中簡單題是否因為簡單而成功率接近 100%（天花板效應）")
    print("  • 國中複雜題是否有修復空間（Healer 的發揮餘地）")
    print("  • 複雜度 3 vs 1 的成功率差異")
    print()
    
    # 檢查文件存在性
    missing = [skill_id for skill_id, info in SKILLS_TO_TEST.items() 
               if not check_skill_exists(info["file"])]
    
    if missing:
        print("【⚠️  缺失的技能】")
        for skill_id in missing:
            print(f"  • {skill_id}: {SKILLS_TO_TEST[skill_id]['file']}")
        print()
    
    print("=" * 80)
    print()

def prepare_test_report():
    """準備測試報告框架"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_plan": "高中 vs 國中技能成功率對比",
        "skills": {},
        "summary": {}
    }
    
    for skill_id, info in SKILLS_TO_TEST.items():
        report["skills"][skill_id] = {
            "info": info,
            "exists": check_skill_exists(info["file"]),
            "iterations": []
        }
    
    return report

if __name__ == "__main__":
    print_test_plan()
    
    # 準備報告
    report = prepare_test_report()
    
    print("📋 測試報告框架已準備")
    print()
    print(f"報告將包含：")
    print(f"  • {len(SKILLS_TO_TEST)} 個技能")
    print(f"  • 每個技能 5 次生成")
    print(f"  • 成功率、修復率、代碼品質指標")
    print()
    print("✅ 準備完成，等待執行生成測試")
