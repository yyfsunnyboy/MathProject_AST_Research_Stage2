#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
快速验证：高中5个甜蜜点技能的生成能力
=============================================================================

目的：
  快速测试系统在高中核心技能上的表现
  5 个技能 × 3 次 = 15 个测试点
  预计运行时间：10-20 分钟
  
结果将决定：✅ 全选高中 vs ⚠️ 混合策略
"""

import sys
import os
import json
import time
import shutil
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from collections import defaultdict

# ============================================================================
# 路径设定
# ============================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = current_dir
while not os.path.exists(os.path.join(project_root, 'app.py')):
    parent = os.path.dirname(project_root)
    if parent == project_root:
        print("❌ 错误：无法定位项目根目录")
        sys.exit(1)
    project_root = parent

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app import create_app
from core.code_generator import auto_generate_skill_code

# ============================================================================
# 高中甜蜜点技能（5 个代表性技能，600-760 行）
# ============================================================================
QUICK_TEST_SKILLS = {
    "gh_ApplicationsOfDerivatives": {
        "backup_file": "skills/backup_GenByGemini/gh_ApplicationsOfDerivatives.py",
        "lines": 758,
        "concept": "微积分应用",
        "priority": 1
    },
    "gh_UsingSuperpositionToFindExtrema": {
        "backup_file": "skills/backup_GenByGemini/gh_UsingSuperpositionToFindExtrema.py",
        "lines": 656,
        "concept": "优化问题",
        "priority": 1
    },
    "gh_ApplicationsOfExponentialFunctions": {
        "backup_file": "skills/backup_GenByGemini/gh_ApplicationsOfExponentialFunctions.py",
        "lines": 612,
        "concept": "指数函数应用",
        "priority": 2
    },
    "gh_JudgingTheRelationshipOfCircleAndLine": {
        "backup_file": "skills/backup_GenByGemini/gh_JudgingTheRelationshipOfCircleAndLine.py",
        "lines": 606,
        "concept": "解析几何",
        "priority": 2
    },
    "gh_RootsOfNthDegreeEquations": {
        "backup_file": "skills/backup_GenByGemini/gh_RootsOfNthDegreeEquations.py",
        "lines": 601,
        "concept": "方程求根",
        "priority": 2
    },
}

ITERATIONS = 3  # 快速测试：每个技能只试 3 次

class QuickValidator:
    def __init__(self):
        self.results = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "test_type": "高中甜蜜点快速验证",
                "total_skills": len(QUICK_TEST_SKILLS),
                "iterations_per_skill": ITERATIONS,
                "total_test_points": len(QUICK_TEST_SKILLS) * ITERATIONS,
            },
            "skills": {},
            "summary": {}
        }
        self.skills_dir = os.path.join(project_root, 'skills')
        
    def prepare_skills(self):
        """复制备份技能到 skills/ 目录"""
        print("\n" + "="*80)
        print("📋 [Step 1] 准备高中技能文件")
        print("="*80)
        
        for skill_name, info in QUICK_TEST_SKILLS.items():
            backup_path = os.path.join(project_root, info["backup_file"])
            skill_id = Path(backup_path).stem
            skill_path = os.path.join(self.skills_dir, f"{skill_id}.py")
            
            if not os.path.exists(backup_path):
                print(f"  ❌ {skill_name}: 备份文件不存在 {backup_path}")
                continue
            
            try:
                shutil.copy(backup_path, skill_path)
                print(f"  ✅ {skill_name} ({info['lines']}行): 已准备")
            except Exception as e:
                print(f"  ❌ {skill_name}: 复制失败 {e}")
    
    def run_quick_test(self):
        """执行快速测试"""
        print("\n" + "="*80)
        print("🧪 [Step 2] 快速生成测试 (5个技能 × 3次 = 15个测试点)")
        print("="*80)
        print()
        
        total_iterations = len(QUICK_TEST_SKILLS) * ITERATIONS
        pbar = tqdm(total=total_iterations, desc="总进度", unit="test", ncols=100)
        
        for skill_name, info in QUICK_TEST_SKILLS.items():
            backup_path = os.path.join(project_root, info["backup_file"])
            skill_id = Path(backup_path).stem
            
            self.results["skills"][skill_name] = {
                "info": {
                    "skill_id": skill_id,
                    "lines": info["lines"],
                    "concept": info["concept"],
                    "priority": info["priority"],
                },
                "iterations": []
            }
            
            for iteration in range(ITERATIONS):
                pbar.set_description(f"{skill_name} ({iteration+1}/{ITERATIONS})")
                
                try:
                    # 调用生成函数
                    is_ok, msg, metrics = auto_generate_skill_code(
                        skill_id,
                        queue=None,
                        ablation_id=3,  # 完整系统
                        model_size_class="14B",
                        prompt_level="Full-Healing"
                    )
                    
                    iter_result = {
                        "iteration": iteration + 1,
                        "success": is_ok,
                        "valid": metrics.get('is_valid', False) if is_ok else False,
                        "repairs": metrics.get('fixes', 0) if is_ok else 0,
                        "message": msg,
                    }
                    
                    self.results["skills"][skill_name]["iterations"].append(iter_result)
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
        """分析结果"""
        print("\n" + "="*80)
        print("📊 [Step 3] 快速分析")
        print("="*80)
        print()
        
        total_success = 0
        total_tests = 0
        skill_results = {}
        
        for skill_name, skill_data in self.results["skills"].items():
            info = skill_data["info"]
            success_count = 0
            total_count = 0
            
            for iter_data in skill_data["iterations"]:
                total_count += 1
                if iter_data.get("success") and iter_data.get("valid"):
                    success_count += 1
            
            total_tests += total_count
            total_success += success_count
            success_rate = (success_count / total_count * 100) if total_count > 0 else 0
            
            skill_results[skill_name] = {
                "success": success_count,
                "total": total_count,
                "rate": success_rate
            }
            
            status = "✅" if success_rate >= 80 else "⚠️ " if success_rate >= 60 else "❌"
            print(f"  {status} {skill_name:<45} | {success_count}/{total_count} = {success_rate:5.1f}% | {info['concept']}")
        
        print()
        print("="*80)
        print("🎯 【快速结论】")
        print("="*80)
        
        overall_rate = (total_success / total_tests * 100) if total_tests > 0 else 0
        print(f"\n  总体成功率：{total_success}/{total_tests} = {overall_rate:.1f}%")
        print()
        
        if overall_rate >= 80:
            print("  ✅ 【非常好】系统稳定可靠")
            print("     → 建议：全选高中 20 个技能！")
            print("     → 策略：简单→中等→困难，展现系统完整能力")
            confidence = "HIGH"
        elif overall_rate >= 70:
            print("  ⚠️  【可以接受】系统基本稳定")
            print("     → 建议：选 15 个高中 + 5 个国中辅助")
            print("     → 策略：主要展现高中，轻度展示修复能力")
            confidence = "MEDIUM"
        elif overall_rate >= 60:
            print("  ⚠️  【需要优化】系统需要改进")
            print("     → 建议：回到原方案（国中为主）")
            print("     → 原因：有数据支撑『高中题实际难度高』")
            confidence = "LOW"
        else:
            print("  ❌ 【系统有问题】成功率过低")
            print("     → 建议：调查生成问题，做 debug")
            confidence = "CRITICAL"
        
        self.results["summary"] = {
            "overall_success_rate": f"{overall_rate:.1f}%",
            "total_success": total_success,
            "total_tests": total_tests,
            "confidence_level": confidence,
            "skill_results": skill_results
        }
        
        print()
        print("="*80)
        print(f"【信心级别】{confidence}")
        print("="*80)
    
    def save_results(self):
        """保存结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(project_root, f"quick_validation_highschool_{timestamp}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 结果已保存: {output_file}")

def main():
    print("="*80)
    print("🧪 高中甜蜜点技能快速验证")
    print("="*80)
    print()
    print("这个测试将在 10-20 分钟内回答：")
    print("  ❓ 系统在高中核心技能上是否稳定？")
    print("  ❓ 我们应该选全高中还是混合策略？")
    print()
    
    app = create_app()
    with app.app_context():
        import logging
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        
        validator = QuickValidator()
        
        # Step 1: 准备
        validator.prepare_skills()
        
        # Step 2: 执行
        validator.run_quick_test()
        
        # Step 3: 分析
        validator.analyze_results()
        
        # Step 4: 保存
        validator.save_results()
        
        print("\n" + "="*80)
        print("🎉 快速验证完成！")
        print("="*80)
        print("\n✨ 根据上述结果，我们现在有数据支撑来做最终决策 ✨\n")

if __name__ == "__main__":
    main()
