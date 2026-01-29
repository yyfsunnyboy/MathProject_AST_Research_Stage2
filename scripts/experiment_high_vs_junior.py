#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
高中 vs 國中技能生成實驗 (High School vs Junior High Comparative Study)

目的：
  判斷是否高中簡單題因複雜度低而達到「天花板效應」（>95% 成功率），
  還是有修復空間。據此決定科技盃選題策略。

設計：
  • 高中: 4 個技能（複雜度 1-3 各異）× 5 次迭代 = 20 個測試點
  • 國中: 4 個技能（複雜度 1-3 各異）× 5 次迭代 = 20 個測試點
  • 共計: 40 個測試點
  • 測量指標: 成功率、修復率、生成時間、代碼品質

核心邏輯：
  1. 從備份技能複製到 skills/ 目錄
  2. 呼叫 auto_generate_skill_code() 生成 5 次
  3. 記錄成功/失敗、修復情況
  4. 比較高中 vs 國中的成功率分佈

輸出：
  • experiment_result_*.json: 完整測試數據
  • 統計報告: success_rate_by_complexity.txt

=============================================================================
"""

import sys
import os
import json
import time
import shutil
import logging
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from collections import defaultdict

# ============================================================================
# 路徑設定
# ============================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = current_dir
while not os.path.exists(os.path.join(project_root, 'app.py')):
    parent = os.path.dirname(project_root)
    if parent == project_root:
        print("❌ 錯誤：無法定位專案根目錄")
        sys.exit(1)
    project_root = parent

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app import create_app
from models import db, SkillInfo
from core.code_generator import auto_generate_skill_code

# ============================================================================
# 待測技能清單
# ============================================================================
SKILLS_TO_TEST = {
    "高中_複雜度3": {
        "backup_file": "skills/backup_GenByGemini/gh_PolynomialInequalities.py",
        "category": "高中",
        "complexity": 3,
        "lines": 931
    },
    "高中_複雜度2a": {
        "backup_file": "skills/backup_GenByGemini/gh_ApplicationsOfDerivatives.py",
        "category": "高中",
        "complexity": 2,
        "lines": 758
    },
    "高中_複雜度2b": {
        "backup_file": "skills/backup_GenByGemini/gh_RealExponentsAndLaws.py",
        "category": "高中",
        "complexity": 2,
        "lines": 714
    },
    "高中_複雜度1": {
        "backup_file": "skills/backup_GenByGemini/gh_GeometricMeaningOfLinearEquations.py",
        "category": "高中",
        "complexity": 1,
        "lines": 497
    },
    "國中_複雜度3a": {
        "backup_file": "skills/backup_20260129/jh_數學2下_FunctionGraph.py",
        "category": "國中",
        "complexity": 3,
        "lines": 794
    },
    "國中_複雜度3b": {
        "backup_file": "skills/backup_20260129/jh_數學2上_FourOperationsOfRadicals.py",
        "category": "國中",
        "complexity": 3,
        "lines": 864
    },
    "國中_複雜度2": {
        "backup_file": "skills/backup_20260129/jh_數學1上_IntegerAdditionOperation.py",
        "category": "國中",
        "complexity": 2,
        "lines": 425
    },
    "國中_複雜度1": {
        "backup_file": "skills/backup_20260129/jh_數學1上_ComparingNumbers.py",
        "category": "國中",
        "complexity": 1,
        "lines": 227
    },
}

ITERATIONS = 5  # 每個技能生成 5 次

class ExperimentRunner:
    def __init__(self, app_context):
        self.app_context = app_context
        self.results = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_skills": len(SKILLS_TO_TEST),
                "iterations_per_skill": ITERATIONS,
                "total_test_points": len(SKILLS_TO_TEST) * ITERATIONS,
            },
            "skills": {},
            "summary": {}
        }
        self.skills_dir = os.path.join(project_root, 'skills')
        
    def prepare_skills(self):
        """複製備份技能到 skills/ 目錄"""
        print("\n" + "="*80)
        print("📋 [Step 1] 準備技能檔案")
        print("="*80)
        
        for skill_name, info in SKILLS_TO_TEST.items():
            backup_path = os.path.join(project_root, info["backup_file"])
            skill_id = Path(backup_path).stem
            skill_path = os.path.join(self.skills_dir, f"{skill_id}.py")
            
            if not os.path.exists(backup_path):
                print(f"  ❌ {skill_name}: 備份檔案不存在 {backup_path}")
                continue
            
            # 複製備份到 skills/
            try:
                shutil.copy(backup_path, skill_path)
                print(f"  ✅ {skill_name} ({skill_id}): 已準備")
            except Exception as e:
                print(f"  ❌ {skill_name}: 複製失敗 {e}")
    
    def run_experiment(self):
        """執行完整實驗"""
        print("\n" + "="*80)
        print("🧪 [Step 2] 執行生成實驗")
        print("="*80)
        print(f"  共 {len(SKILLS_TO_TEST)} 個技能 × {ITERATIONS} 次迭代 = {len(SKILLS_TO_TEST) * ITERATIONS} 個測試點")
        print()
        
        total_iterations = len(SKILLS_TO_TEST) * ITERATIONS
        pbar = tqdm(total=total_iterations, desc="總進度", unit="test", ncols=100)
        
        for skill_name, info in SKILLS_TO_TEST.items():
            backup_path = os.path.join(project_root, info["backup_file"])
            skill_id = Path(backup_path).stem
            
            self.results["skills"][skill_name] = {
                "info": {
                    "skill_id": skill_id,
                    "category": info["category"],
                    "complexity": info["complexity"],
                    "lines": info["lines"],
                },
                "iterations": []
            }
            
            for iteration in range(ITERATIONS):
                pbar.set_description(f"{skill_name} ({iteration+1}/{ITERATIONS})")
                
                try:
                    # 呼叫 auto_generate_skill_code()
                    # ablation_id=3 (使用完整的 Healer)
                    is_ok, msg, metrics = auto_generate_skill_code(
                        skill_id,
                        queue=None,
                        ablation_id=3,  # 完整系統
                        model_size_class="14B",
                        prompt_level="Full-Healing"
                    )
                    
                    # 記錄結果
                    iter_result = {
                        "iteration": iteration + 1,
                        "success": is_ok,
                        "valid": metrics.get('is_valid', False) if is_ok else False,
                        "repairs": metrics.get('fixes', 0) if is_ok else 0,
                        "generation_time": metrics.get('generation_time', 0) if is_ok else 0,
                        "message": msg,
                    }
                    
                    self.results["skills"][skill_name]["iterations"].append(iter_result)
                    
                    # 更新進度條
                    pbar.update(1)
                    
                except Exception as e:
                    print(f"  ❌ {skill_name} iteration {iteration+1}: {e}")
                    self.results["skills"][skill_name]["iterations"].append({
                        "iteration": iteration + 1,
                        "success": False,
                        "error": str(e)
                    })
                    pbar.update(1)
        
        pbar.close()
    
    def analyze_results(self):
        """分析結果"""
        print("\n" + "="*80)
        print("📊 [Step 3] 結果分析")
        print("="*80)
        
        # 計算統計
        stats_by_category_complexity = defaultdict(lambda: {"success": 0, "total": 0, "repairs": []})
        
        for skill_name, skill_data in self.results["skills"].items():
            info = skill_data["info"]
            category = info["category"]
            complexity = info["complexity"]
            key = f"{category}_Complexity{complexity}"
            
            for iter_data in skill_data["iterations"]:
                stats_by_category_complexity[key]["total"] += 1
                
                if iter_data.get("success") and iter_data.get("valid"):
                    stats_by_category_complexity[key]["success"] += 1
                    repairs = iter_data.get("repairs", 0)
                    stats_by_category_complexity[key]["repairs"].append(repairs)
        
        # 組織統計
        self.results["summary"]["by_category_complexity"] = {}
        for key, stats in sorted(stats_by_category_complexity.items()):
            total = stats["total"]
            success = stats["success"]
            success_rate = (success / total * 100) if total > 0 else 0
            avg_repairs = sum(stats["repairs"]) / len(stats["repairs"]) if stats["repairs"] else 0
            
            self.results["summary"]["by_category_complexity"][key] = {
                "success_rate": f"{success_rate:.1f}%",
                "success_count": success,
                "total": total,
                "avg_repairs": f"{avg_repairs:.1f}",
            }
            
            print(f"  {key:30s}: {success:2d}/{total:2d} = {success_rate:5.1f}% | 平均修復: {avg_repairs:.1f}x")
        
        # 高中 vs 國中對比
        print("\n【高中 vs 國中對比】")
        high_school = defaultdict(lambda: {"success": 0, "total": 0})
        junior_high = defaultdict(lambda: {"success": 0, "total": 0})
        
        for skill_name, skill_data in self.results["skills"].items():
            info = skill_data["info"]
            category = info["category"]
            complexity = info["complexity"]
            
            target = high_school if category == "高中" else junior_high
            key = f"Complexity{complexity}"
            
            for iter_data in skill_data["iterations"]:
                target[key]["total"] += 1
                if iter_data.get("success") and iter_data.get("valid"):
                    target[key]["success"] += 1
        
        print("\n  📍 高中技能:")
        for complexity in [1, 2, 3]:
            key = f"Complexity{complexity}"
            if key in high_school:
                s = high_school[key]["success"]
                t = high_school[key]["total"]
                rate = (s / t * 100) if t > 0 else 0
                print(f"    • 複雜度{complexity}: {s}/{t} = {rate:.1f}%")
        
        print("\n  📍 國中技能:")
        for complexity in [1, 2, 3]:
            key = f"Complexity{complexity}"
            if key in junior_high:
                s = junior_high[key]["success"]
                t = junior_high[key]["total"]
                rate = (s / t * 100) if t > 0 else 0
                print(f"    • 複雜度{complexity}: {s}/{t} = {rate:.1f}%")
    
    def save_results(self):
        """儲存結果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(project_root, f"experiment_result_{timestamp}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 完整結果已儲存: {output_file}")
        print(f"   文件大小: {os.path.getsize(output_file) / 1024:.1f} KB")

def main():
    print("="*80)
    print("🧪 高中 vs 國中技能生成能力對比實驗")
    print("="*80)
    
    app = create_app()
    with app.app_context():
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        
        runner = ExperimentRunner(app)
        
        # Step 1: 準備
        runner.prepare_skills()
        
        # Step 2: 執行
        runner.run_experiment()
        
        # Step 3: 分析
        runner.analyze_results()
        
        # Step 4: 儲存
        runner.save_results()
        
        print("\n" + "="*80)
        print("🎉 實驗完成！")
        print("="*80)

if __name__ == "__main__":
    main()
