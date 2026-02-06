# -*- coding: utf-8 -*-
"""
=============================================================================
【旺宏科學獎 / 科展專用】複合式 AI 對比實驗自動化工具（3×3 設計）
=============================================================================

╔═══════════════════════════════════════════════════════════════════════════╗
║  程式名稱: competition_benchmark.py                                        ║
║  研究主題: 複合式 AI 架構降低數學題庫生成成本之研究                          ║
║  用途分類: 大規模對比實驗執行器 / 量化數據收集工具                          ║
║  實驗設計: 3×3 完全因子設計（Full Factorial Design）                      ║
╚═══════════════════════════════════════════════════════════════════════════╝

【研究核心問題】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
「能否透過自動修復機制（Active Healer），使小型 Local AI（14B）
 達到大型 Cloud AI（Gemini Pro）的程式生成質量？」

【3×3 實驗設計】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
因子 1: 模型大小（Model Size）
  - 7B:  Qwen 2.5-Coder 7B（本地小模型）
  - 14B: Qwen 2.5-Coder 14B（本地中模型）
  - Cloud: Gemini Pro（雲端大模型）

因子 2: Prompt 策略（Prompt Strategy）
  - Level 1: 直覺 Prompt（Bare Prompt）
  - Level 2: MASTER_SPEC（結構化規格）
  - Level 3: MASTER_SPEC + Active Healer（規格 + 修復）

實驗矩陣（9 組）：
┌────────┬─────────────┬─────────────┬─────────────┐
│        │   Level 1   │   Level 2   │   Level 3   │
│        │ (Bare)      │ (SPEC)      │ (SPEC+Heal) │
├────────┼─────────────┼─────────────┼─────────────┤
│ 7B     │ A1 ❌       │ A2 ⚠️        │ A3 ✅       │
│ 14B    │ B1 ❌       │ B2 ⚙️        │ B3 🏆       │
│ Cloud  │ C1 ⚠️        │ C2 ✅       │ C3 🔝       │
└────────┴─────────────┴─────────────┴─────────────┘

【核心假設】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
H1: Healer 對小模型幫助更大（交互作用效應）
H2: B3（14B + SPEC + Healer）≈ C2（Cloud + SPEC）
H3: B3 成本僅 C2 的 2%（$0.001 vs $0.05）
H4: Active Healer 可提升語法正確率 30-40%（7B: 30% → 80%）

【本程式的目的】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1️⃣  自動化執行 9 組對比實驗（每組 100+ 次測試）
2️⃣  收集量化數據（語法率、邏輯率、成本、速度、修復次數）
3️⃣  生成實驗報告（CSV 格式，可直接用於統計分析）
4️⃣  記錄到資料庫（experiment_log 表，供後續分析）
5️⃣  支援雙因子 ANOVA 和交互作用檢驗
  - 預期語法正確率: 95%
  - 預期邏輯正確率: 90%

【本程式的目的】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1️⃣  自動化執行四組對比實驗（每組 100+ 次測試）
2️⃣  收集量化數據（語法率、邏輯率、成本、速度、修復次數）
3️⃣  生成實驗報告（CSV 格式，可直接用於統計分析）
4️⃣  記錄到資料庫（experiment_log 表，供後續分析）

【主要功能】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ 功能 1: 實驗流程自動化
   - 自動生成 MASTER_SPEC（Architect 階段）
   - 自動生成代碼（Coder 階段）
   - 自動執行修復（Healer 階段，如果啟用）
   - 自動驗證結果（語法檢查 + 邏輯檢查）

✨ 功能 2: 數據收集與記錄
   - 記錄每次實驗的詳細數據（時間、Token、錯誤、修復）
   - 即時保存（防止中途中斷）
   - 雙重記錄（CSV 文件 + 資料庫）

✨ 功能 3: 統計分析與報告
   - 自動計算各組的成功率、成本、質量/成本比
   - 生成對比表格（適合直接貼到論文或 PPT）
   - 輸出詳細日誌（每次實驗的完整記錄）

【評估指標】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. **語法正確率** = AST Parse 成功次數 / 總實驗次數
2. **邏輯正確率** = Dynamic Sampling 通過次數 / 總實驗次數
3. **修復成功率** = 修復後通過次數 / 原始錯誤次數
4. **質量/成本比** = (邏輯正確率 / 成本) × 100
5. **平均生成時間** = 總生成時間 / 實驗次數

【使用方式】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
方式 1 (完整實驗 - 需時數小時):
  $ python scripts/competition_benchmark.py
  → 執行所有技能 × 所有組別 × 10 次重複

方式 2 (小規模測試 - 推薦先執行):
  1. 編輯本文件 Line 90-95
  2. 修改 "test_skills" 為 2-3 個技能
  3. 修改 "trials_per_skill" 為 3
  4. 執行程式

輸出結果:
  - CSV 摘要: reports/competition_experiments/experiment_summary_YYYYMMDD.csv
  - CSV 詳細: reports/competition_experiments/experiment_details_YYYYMMDD.csv
  - 資料庫: experiment_log 表（可用 SQL 查詢）

【資料庫整合】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
每次實驗自動記錄到 experiment_log 表，包含：
  - 實驗識別：skill_id, experiment_batch, experiment_group
  - AI 配置：model_name, model_size_class, prompt_level
  - 成本追蹤：prompt_tokens, completion_tokens, total_tokens
  - 質量評估：is_success, is_executable, score_syntax, score_math
  - 修復統計：regex_fix_count, logic_fix_count, ast_repair_count
  - 代碼保存：raw_response, final_code

查詢範例:
  SELECT experiment_group, AVG(score_math), AVG(total_tokens)
  FROM experiment_log
  WHERE experiment_batch = '2026-01-27_full_test'
  GROUP BY experiment_group;

【版本資訊】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
版本: V1.0
日期: 2026-01-27
作者: Math AI Project Team
競賽: 旺宏科學獎 / 中學科展
依賴: flask, sqlalchemy, ast, csv

【相關文件】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 研究計畫: docs/競賽文件/旺宏科學獎_研究計畫.md
- 快速開始: docs/競賽文件/快速開始指南.md
- 資料庫設計: docs/競賽文件/資料庫設計驗證報告.md
- 可視化工具: scripts/visualize_healer.py

=============================================================================
"""

import os
import sys
import json
import time
import csv
from datetime import datetime
from pathlib import Path

# 添加專案根目錄到 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask
from models import db, SkillInfo, ExperimentLog
from config import Config
from core.code_generator import auto_generate_skill_code
from core.prompt_architect import generate_v15_spec
import ast

# ==============================================================================
# 實驗配置（3×3 因子設計）
# ==============================================================================

EXPERIMENT_CONFIG = {
    # 3×3 實驗組配置
    # 橫軸：模型大小 (7B / 14B / Cloud)
    # 縱軸：Prompt 策略 (Bare / MASTER / MASTER+Healer)
    
    "groups": {
        # ========== 7B 模型系列 ==========
        "A1_7b_bare": {
            "name": "A1: Qwen 7B + 直覺 Prompt",
            "model": "qwen2.5-coder:7b",
            "model_size_class": "7B",
            "prompt_level": "Bare",
            "use_master_spec": False,
            "healer": False,
            "cost_per_skill": 0.000
        },
        "A2_7b_master": {
            "name": "A2: Qwen 7B + MASTER_SPEC",
            "model": "qwen2.5-coder:7b",
            "model_size_class": "7B",
            "prompt_level": "Engineered",
            "use_master_spec": True,
            "healer": False,
            "cost_per_skill": 0.000
        },
        "A3_7b_healer": {
            "name": "A3: Qwen 7B + MASTER + Healer",
            "model": "qwen2.5-coder:7b",
            "model_size_class": "7B",
            "prompt_level": "Self-Healing",
            "use_master_spec": True,
            "healer": True,
            "cost_per_skill": 0.001
        },
        
        # ========== 14B 模型系列 ==========
        "B1_14b_bare": {
            "name": "B1: Qwen 14B + 直覺 Prompt",
            "model": "qwen2.5-coder:14b",
            "model_size_class": "14B",
            "prompt_level": "Bare",
            "use_master_spec": False,
            "healer": False,
            "cost_per_skill": 0.000
        },
        "B2_14b_master": {
            "name": "B2: Qwen 14B + MASTER_SPEC",
            "model": "qwen2.5-coder:14b",
            "model_size_class": "14B",
            "prompt_level": "Engineered",
            "use_master_spec": True,
            "healer": False,
            "cost_per_skill": 0.000
        },
        "B3_14b_healer": {
            "name": "B3: Qwen 14B + MASTER + Healer 🎯",
            "model": "qwen2.5-coder:14b",
            "model_size_class": "14B",
            "prompt_level": "Self-Healing",
            "use_master_spec": True,
            "healer": True,
            "cost_per_skill": 0.001
        },
        
        # ========== Cloud Pro 系列 ==========
        "C1_cloud_bare": {
            "name": "C1: Gemini Pro + 直覺 Prompt",
            "model": "gemini-pro",
            "model_size_class": "Cloud",
            "prompt_level": "Bare",
            "use_master_spec": False,
            "healer": False,
            "cost_per_skill": 0.030
        },
        "C2_cloud_master": {
            "name": "C2: Gemini Pro + MASTER_SPEC",
            "model": "gemini-pro",
            "model_size_class": "Cloud",
            "prompt_level": "Engineered",
            "use_master_spec": True,
            "healer": False,
            "cost_per_skill": 0.050
        },
        "C3_cloud_healer": {
            "name": "C3: Gemini Pro + MASTER + Healer",
            "model": "gemini-pro",
            "model_size_class": "Cloud",
            "prompt_level": "Self-Healing",
            "use_master_spec": True,
            "healer": True,
            "cost_per_skill": 0.050
        }
    },
    
    # 測試技能列表（可擴展到 20 個）
    "test_skills": [
        "jh_數學1上_IntegerAdditionOperation",
        "jh_數學1上_IntegerSubtractionOperation",
        "jh_數學1上_MixedIntegerAdditionAndSubtraction",
        # 可以添加更多技能點，目標 20 個
    ],
    
    # 每個技能的測試次數
    "trials_per_skill": 10,
    
    # 實驗批次名稱（用於區分不同實驗輪次）
    "experiment_batch": f"3x3_design_{datetime.now().strftime('%Y%m%d')}",
    
    # 輸出目錄
    "output_dir": "reports/competition_experiments"
}

# ==============================================================================
# 實驗執行器
# ==============================================================================

class CompetitionBenchmark:
    """科學競賽實驗執行器"""
    
    def __init__(self, app):
        self.app = app
        self.results = []
        self.output_dir = Path(EXPERIMENT_CONFIG["output_dir"])
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def check_syntax(self, code_str):
        """檢查語法正確性"""
        try:
            ast.parse(code_str)
            return True, None
        except SyntaxError as e:
            return False, str(e)
    
    def check_logic(self, skill_file_path):
        """檢查邏輯正確性（執行 generate 函數）"""
        try:
            # 動態導入技能模組
            import importlib.util
            spec = importlib.util.spec_from_file_location("skill_module", skill_file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 執行 5 次 generate
            for i in range(5):
                q, a = module.generate()
                if not q or not a:
                    return False, f"Empty output at iteration {i+1}"
            
            return True, None
        except Exception as e:
            return False, str(e)
    
    def run_single_experiment(self, skill_id, group_name, group_config):
        """執行單次實驗 + 完整資料庫記錄"""
        print(f"\n{'='*60}")
        print(f"Skill: {skill_id}")
        print(f"Group: {group_name} - {group_config['name']}")
        print(f"{'='*60}")
        
        start_time = time.time()
        result = {
            "skill_id": skill_id,
            "group": group_name,
            "timestamp": datetime.now().isoformat(),
            "syntax_pass": False,
            "logic_pass": False,
            "generation_time": 0,
            "cost": group_config["cost_per_skill"],
            "errors": [],
            "healer_enabled": group_config["healer"]
        }
        
        # 資料庫記錄變數
        raw_response = ""
        final_code = ""
        healing_stats = {
            "regex_fix_count": 0,
            "logic_fix_count": 0,
            "ast_repair_count": 0,
            "garbage_cleaner_count": 0,
            "eval_eliminator_count": 0
        }
        prompt_tokens = 0
        completion_tokens = 0
        spec_prompt_id = None
        
        try:
            with self.app.app_context():
                # Step 1: 生成 MASTER_SPEC (Architect)
                if group_config["architect"] == "gemini":
                    print("[Architect] Using Gemini Flash...")
                    spec_result = generate_v15_spec(skill_id, model_tag="cloud_pro")
                else:
                    print("[Architect] Using Local AI...")
                    spec_result = generate_v15_spec(skill_id, model_tag="local_14b")
                
                if not spec_result['success']:
                    result["errors"].append(f"Architect failed: {spec_result.get('message')}")
                    self._save_experiment_log(skill_id, group_name, group_config, result, 
                                             raw_response, final_code, healing_stats, 
                                             prompt_tokens, completion_tokens, spec_prompt_id)
                    return result
                
                # 取得 MASTER_SPEC 的 prompt ID
                spec_prompt_id = spec_result.get('prompt_id')
                
                # Step 2: 生成代碼 (Coder)
                if group_config["coder"] == "gemini":
                    print("[Coder] Using Gemini Pro...")
                    coder_model = "gemini-pro"
                else:
                    print("[Coder] Using Qwen 14B...")
                    coder_model = "qwen2.5-coder:14b"
                
                # Step 3: 自動生成（包含 Healer）
                gen_result = auto_generate_skill_code(
                    skill_id=skill_id,
                    model_tag=group_config.get("model_tag", "local_14b"),
                    coder_model=coder_model,
                    enable_healer=group_config["healer"]
                )
                
                result["generation_time"] = time.time() - start_time
                
                # 提取詳細信息
                raw_response = gen_result.get('raw_response', '')
                final_code = gen_result.get('final_code', '')
                healing_stats = gen_result.get('healing_stats', healing_stats)
                prompt_tokens = gen_result.get('prompt_tokens', 0)
                completion_tokens = gen_result.get('completion_tokens', 0)
                
                if not gen_result['success']:
                    result["errors"].append(f"Coder failed: {gen_result.get('message')}")
                    self._save_experiment_log(skill_id, group_name, group_config, result, 
                                             raw_response, final_code, healing_stats, 
                                             prompt_tokens, completion_tokens, spec_prompt_id)
                    return result
                
                # Step 4: 語法檢查
                skill_file = f"skills/{skill_id}.py"
                with open(skill_file, 'r', encoding='utf-8') as f:
                    final_code = f.read()  # 更新為實際檔案內容
                
                syntax_ok, syntax_err = self.check_syntax(final_code)
                result["syntax_pass"] = syntax_ok
                if not syntax_ok:
                    result["errors"].append(f"Syntax Error: {syntax_err}")
                    self._save_experiment_log(skill_id, group_name, group_config, result, 
                                             raw_response, final_code, healing_stats, 
                                             prompt_tokens, completion_tokens, spec_prompt_id)
                    return result
                
                # Step 5: 邏輯檢查
                logic_ok, logic_err = self.check_logic(skill_file)
                result["logic_pass"] = logic_ok
                if not logic_ok:
                    result["errors"].append(f"Logic Error: {logic_err}")
                
                print(f"✅ Success! Time: {result['generation_time']:.2f}s")
                
                # 成功完成，記錄到資料庫
                self._save_experiment_log(skill_id, group_name, group_config, result, 
                                         raw_response, final_code, healing_stats, 
                                         prompt_tokens, completion_tokens, spec_prompt_id)
                
        except Exception as e:
            result["errors"].append(f"Unexpected error: {str(e)}")
            print(f"❌ Failed: {str(e)}")
            # 即使失敗也記錄
            self._save_experiment_log(skill_id, group_name, group_config, result, 
                                     raw_response, final_code, healing_stats, 
                                     prompt_tokens, completion_tokens, spec_prompt_id)
        
        return result
    
    def _save_experiment_log(self, skill_id, group_name, group_config, result, 
                             raw_response, final_code, healing_stats, 
                             prompt_tokens, completion_tokens, spec_prompt_id):
        """儲存實驗記錄到資料庫"""
        try:
            log_entry = ExperimentLog(
                skill_id=skill_id,
                experiment_group=group_name,  # 'A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3'
                model_name=group_config.get('coder_model', group_config.get('model', 'unknown')),
                model_size_class=group_config.get('model_size_class', 'Unknown'),
                prompt_level=group_config.get('prompt_level', 'Unknown'),
                use_master_spec=group_config.get('use_master_spec', False),
                spec_prompt_id=spec_prompt_id,
                raw_response=raw_response,
                final_code=final_code,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                is_success=result['syntax_pass'] and result['logic_pass'],
                is_executable=result['syntax_pass'],
                score_syntax=1.0 if result['syntax_pass'] else 0.0,
                score_math=1.0 if result['logic_pass'] else 0.0,
                score_visual=0.0,  # 暫不評估
                healing_duration=result['generation_time'],
                regex_fix_count=healing_stats.get('regex_fix_count', 0),
                logic_fix_count=healing_stats.get('logic_fix_count', 0),
                ast_repair_count=healing_stats.get('ast_repair_count', 0),
                garbage_cleaner_count=healing_stats.get('garbage_cleaner_count', 0),
                eval_eliminator_count=healing_stats.get('eval_eliminator_count', 0),
                sampling_success_count=healing_stats.get('sampling_success_count', 0),
                sampling_total_count=healing_stats.get('sampling_total_count', 0)
            )
            
            db.session.add(log_entry)
            db.session.commit()
            print(f"📊 Experiment log saved: ID={log_entry.id}")
            
        except Exception as e:
            print(f"⚠️  Failed to save experiment log: {str(e)}")
            db.session.rollback()
    
    def run_all_experiments(self):
        """執行所有實驗"""
        print("\n" + "="*60)
        print("🔬 開始執行旺宏科學獎實驗")
        print("="*60)
        
        total_experiments = (
            len(EXPERIMENT_CONFIG["test_skills"]) * 
            len(EXPERIMENT_CONFIG["groups"]) * 
            EXPERIMENT_CONFIG["trials_per_skill"]
        )
        
        print(f"📊 實驗規模:")
        print(f"   - 技能數: {len(EXPERIMENT_CONFIG['test_skills'])}")
        print(f"   - 實驗組數: {len(EXPERIMENT_CONFIG['groups'])}")
        print(f"   - 每組重複次數: {EXPERIMENT_CONFIG['trials_per_skill']}")
        print(f"   - 總實驗次數: {total_experiments}")
        print()
        
        exp_count = 0
        
        for skill_id in EXPERIMENT_CONFIG["test_skills"]:
            for group_name, group_config in EXPERIMENT_CONFIG["groups"].items():
                for trial in range(EXPERIMENT_CONFIG["trials_per_skill"]):
                    exp_count += 1
                    print(f"\n[{exp_count}/{total_experiments}] Trial {trial+1}/{EXPERIMENT_CONFIG['trials_per_skill']}")
                    
                    result = self.run_single_experiment(skill_id, group_name, group_config)
                    self.results.append(result)
                    
                    # 即時保存結果（防止中途中斷）
                    self.save_interim_results()
        
        # 最終分析
        self.analyze_and_save()
    
    def save_interim_results(self):
        """即時保存結果（JSON 格式）"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = self.output_dir / f"interim_results_{timestamp}.json"
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
    
    def analyze_and_save(self):
        """分析結果並保存 CSV 報告"""
        print("\n" + "="*60)
        print("📊 分析實驗結果")
        print("="*60)
        
        # 按組別統計
        group_stats = {}
        for group_name in EXPERIMENT_CONFIG["groups"].keys():
            group_results = [r for r in self.results if r["group"] == group_name]
            
            total = len(group_results)
            syntax_pass = sum(1 for r in group_results if r["syntax_pass"])
            logic_pass = sum(1 for r in group_results if r["logic_pass"])
            avg_time = sum(r["generation_time"] for r in group_results) / total if total > 0 else 0
            total_cost = sum(r["cost"] for r in group_results)
            
            group_stats[group_name] = {
                "name": EXPERIMENT_CONFIG["groups"][group_name]["name"],
                "total_experiments": total,
                "syntax_pass_rate": syntax_pass / total * 100 if total > 0 else 0,
                "logic_pass_rate": logic_pass / total * 100 if total > 0 else 0,
                "avg_generation_time": avg_time,
                "total_cost": total_cost,
                "quality_cost_ratio": (logic_pass / total * 100) / (total_cost + 0.001) if total > 0 else 0
            }
        
        # 打印統計結果
        print("\n📈 實驗組對比:")
        print(f"{'組別':<30} {'語法通過率':<12} {'邏輯通過率':<12} {'平均時間':<10} {'總成本':<10} {'質量/成本':<12}")
        print("-" * 100)
        
        for group_name, stats in group_stats.items():
            print(f"{stats['name']:<30} "
                  f"{stats['syntax_pass_rate']:>10.1f}% "
                  f"{stats['logic_pass_rate']:>10.1f}% "
                  f"{stats['avg_generation_time']:>8.2f}s "
                  f"${stats['total_cost']:>8.2f} "
                  f"{stats['quality_cost_ratio']:>10.1f}")
        
        # 保存 CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = self.output_dir / f"experiment_summary_{timestamp}.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'group', 'name', 'total_experiments', 'syntax_pass_rate', 
                'logic_pass_rate', 'avg_generation_time', 'total_cost', 'quality_cost_ratio'
            ])
            writer.writeheader()
            for group_name, stats in group_stats.items():
                writer.writerow({'group': group_name, **stats})
        
        # 保存完整詳細結果
        detailed_csv = self.output_dir / f"experiment_details_{timestamp}.csv"
        with open(detailed_csv, 'w', newline='', encoding='utf-8-sig') as f:
            if self.results:
                writer = csv.DictWriter(f, fieldnames=self.results[0].keys())
                writer.writeheader()
                writer.writerows(self.results)
        
        print(f"\n✅ 結果已保存:")
        print(f"   - 摘要: {csv_file}")
        print(f"   - 詳細: {detailed_csv}")

# ==============================================================================
# Main Entry
# ==============================================================================

def main():
    """主程式"""
    print("=" * 60)
    print("🏆 旺宏科學獎 - 複合式 AI 自動修復機制實驗")
    print("=" * 60)
    
    # 創建 Flask App
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    # 執行實驗
    benchmark = CompetitionBenchmark(app)
    benchmark.run_all_experiments()
    
    print("\n🎉 實驗完成！")

if __name__ == "__main__":
    main()
