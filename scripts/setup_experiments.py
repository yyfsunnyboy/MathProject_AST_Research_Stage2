# -*- coding: utf-8 -*-
"""
實驗架構快速設置
一鍵完成所有初始化工作

使用方式:
    python scripts/setup_experiments.py
"""

import sys
import os
from pathlib import Path

# 加入專案路徑
sys.path.insert(0, os.path.abspath('.'))

def print_header(title):
    """列印標題"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}\n")

def create_directory_structure():
    """建立目錄結構"""
    print_header("📁 建立目錄結構")
    
    directories = [
        "experiments",
        "experiments/golden_prompts",
        "experiments/results",
        "experiments/results/gh_ApplicationsOfDerivatives/Ab1",
        "experiments/results/gh_ApplicationsOfDerivatives/Ab2",
        "experiments/results/gh_ApplicationsOfDerivatives/Ab3",
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ {dir_path}/")
    
    print("\n✅ 目錄結構建立完成")

def create_gitignore():
    """更新 .gitignore"""
    print_header("📝 更新 .gitignore")
    
    gitignore_content = """
# ============================================================================
# Experiments 目錄規則
# ============================================================================

# 忽略所有實驗結果檔案（太多且會變動）
experiments/results/**/*.py
experiments/results/**/*.json

# 保留 Golden Prompts（這些是靜態的，應該被追蹤）
!experiments/golden_prompts/*.txt

# 保留目錄結構（追蹤 .gitkeep）
!experiments/results/**/
!experiments/results/**/.gitkeep
"""
    
    gitignore_path = Path(".gitignore")
    
    # 讀取現有內容
    existing_content = ""
    if gitignore_path.exists():
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
    
    # 如果尚未添加實驗規則，則添加
    if "Experiments 目錄規則" not in existing_content:
        with open(gitignore_path, 'a', encoding='utf-8') as f:
            f.write(gitignore_content)
        print("✅ 已更新 .gitignore")
    else:
        print("ℹ️ .gitignore 已包含實驗規則")

def create_gitkeep_files():
    """在結果目錄中建立 .gitkeep 檔案"""
    print_header("🔖 建立 .gitkeep 檔案")
    
    result_dirs = list(Path("experiments/results").rglob("Ab*"))
    
    for dir_path in result_dirs:
        gitkeep = dir_path / ".gitkeep"
        gitkeep.touch()
        print(f"✅ {gitkeep}")
    
    print(f"\n✅ 已建立 {len(result_dirs)} 個 .gitkeep 檔案")

def export_sample_golden_prompt():
    """匯出範例 Golden Prompt"""
    print_header("📄 匯出範例 Golden Prompt")
    
    try:
        from core.prompts.prompt_builder import PromptBuilder
        
        # 為 gh_ApplicationsOfDerivatives 匯出 Ab1, Ab2, Ab3
        skill_id = "gh_ApplicationsOfDerivatives"
        topic = "多項式函數的導數計算"
        
        master_spec = """【題型描述】求多項式函數的導數

【複雜度要求】
- 多項式次數：3-5 次
- 係數範圍：-10 到 10
- 求導次數：隨機選擇 2 個不同階數

【輸出格式】
- 題目使用 LaTeX 格式
- 答案為純多項式文字"""
        
        textbook_example = """範例：已知 f(x) = 3x³ - 5x² + 2，求 f'(x) 與 f''(x) 的值。
答案：9x² - 10x, 18x - 10"""
        
        for ablation_id in [1, 2, 3]:
            prompt = PromptBuilder.build(
                master_spec=master_spec,
                ablation_id=ablation_id,
                textbook_example=textbook_example,
                topic=topic,
                skill_id=skill_id
            )
            
            filename = f"experiments/golden_prompts/{skill_id}_Ab{ablation_id}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# Golden Prompt - {skill_id} (Ablation {ablation_id})\n")
                f.write(f"# 建立時間: {Path().cwd()}\n\n")
                f.write(prompt)
            
            print(f"✅ {filename} ({len(prompt):,} 字符)")
        
        print("\n✅ 範例 Golden Prompts 匯出完成")
        
    except Exception as e:
        print(f"⚠️ 無法匯出 Golden Prompts: {e}")
        print("   請稍後使用 `python scripts/export_golden_prompts.py` 手動匯出")

def print_next_steps():
    """列印後續步驟"""
    print_header("🎯 後續步驟")
    
    print("""
✅ 實驗架構已設置完成！

📋 接下來您可以：

1. 匯出所有技能的 Golden Prompts：
   python scripts/export_golden_prompts.py --all

2. 執行批次實驗（100 次生成）：
   python scripts/run_batch_experiment.py --skill gh_ApplicationsOfDerivatives --samples 100

3. 遷移現有的 skills/ 檔案（可選）：
   python scripts/migrate_to_experiments.py --dry-run  # 先預覽
   python scripts/migrate_to_experiments.py            # 執行遷移

4. 分析實驗結果：
   python scripts/analyze_experiment_results.py --skill gh_ApplicationsOfDerivatives

📚 詳細說明請參考：
   experiments/README.md
""")

def main():
    print_header("🚀 實驗架構快速設置")
    
    print("這將建立以下結構：")
    print("""
    experiments/
    ├── golden_prompts/          # [輸入] 靜態 Prompt 檔案
    │   ├── {skill_id}_Ab1.txt
    │   ├── {skill_id}_Ab2.txt
    │   └── {skill_id}_Ab3.txt
    │
    └── results/                 # [輸出] 實驗結果
        └── {skill_id}/
            ├── Ab1/
            │   ├── sample_1.py
            │   ├── sample_1.json
            │   └── ...
            ├── Ab2/
            └── Ab3/
    """)
    
    input("\n按 Enter 繼續...")
    
    # 執行設置步驟
    create_directory_structure()
    create_gitignore()
    create_gitkeep_files()
    export_sample_golden_prompt()
    print_next_steps()
    
    print("\n🎉 設置完成！\n")

if __name__ == '__main__':
    main()
