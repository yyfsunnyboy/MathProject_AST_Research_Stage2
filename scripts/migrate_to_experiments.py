# -*- coding: utf-8 -*-
"""
遷移工具：將現有的 skills/ 檔案遷移到新的 experiments/ 結構

使用方式:
    python scripts/migrate_to_experiments.py --dry-run  # 預覽遷移操作
    python scripts/migrate_to_experiments.py            # 執行遷移
"""

import sys
import os
import re
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# 加入專案路徑
sys.path.insert(0, os.path.abspath('.'))

def parse_skill_filename(filename):
    """
    解析技能檔案名稱
    
    範例:
        gh_ApplicationsOfDerivatives_14b_Ab2.py
        -> skill_id: gh_ApplicationsOfDerivatives
           model: 14b
           ablation_id: 2
    """
    pattern = r'^(.+?)_(14b|cloud)_Ab([123])\.py$'
    match = re.match(pattern, filename)
    
    if match:
        return {
            'skill_id': match.group(1),
            'model': match.group(2),
            'ablation_id': int(match.group(3))
        }
    return None

def extract_metadata_from_file(filepath):
    """從檔案標頭提取 metadata"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read(500)  # 只讀前 500 字符
    
    metadata = {}
    
    # 提取標頭資訊
    patterns = {
        'model': r'# Model:\s*(.+?)\s*\|',
        'tokens_in': r'Tokens:\s*In=(\d+)',
        'tokens_out': r'Out=(\d+)',
        'generation_time': r'Performance:\s*([\d.]+)s',
        'created_at': r'Created At:\s*(.+)',
        'strategy': r'Strategy:\s*(.+?)\s*\n'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        if match:
            value = match.group(1).strip()
            # 轉換數值型別
            if key in ['tokens_in', 'tokens_out']:
                metadata[key] = int(value)
            elif key == 'generation_time':
                metadata[key] = float(value)
            else:
                metadata[key] = value
    
    return metadata

def migrate_file(source_path, skill_id, ablation_id, sample_num, dry_run=False):
    """
    遷移單一檔案
    
    Args:
        source_path: 原始檔案路徑
        skill_id: 技能 ID
        ablation_id: Ablation ID
        sample_num: 樣本編號
        dry_run: 是否只預覽不執行
    """
    # 目標目錄
    target_dir = Path(f"experiments/results/{skill_id}/Ab{ablation_id}")
    
    # 目標檔案
    code_file = target_dir / f"sample_{sample_num}.py"
    json_file = target_dir / f"sample_{sample_num}.json"
    
    if dry_run:
        print(f"   [預覽] {source_path.name} -> {code_file.relative_to('experiments/results')}")
        return
    
    # 建立目錄
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # 複製程式碼檔案
    shutil.copy2(source_path, code_file)
    
    # 提取 metadata
    metadata = extract_metadata_from_file(source_path)
    
    # 建立 JSON 報告
    report = {
        "sample_id": sample_num,
        "skill_id": skill_id,
        "ablation_id": ablation_id,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata,
        "validation": {
            "note": "從舊檔案遷移，驗證資訊不完整"
        },
        "file_path": str(code_file.relative_to("experiments/results")),
        "migrated_from": str(source_path)
    }
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ {source_path.name} -> {code_file.name}")

def scan_skills_directory():
    """掃描 skills/ 目錄，找出所有需要遷移的檔案"""
    skills_dir = Path("skills")
    
    if not skills_dir.exists():
        print("❌ skills/ 目錄不存在")
        return []
    
    files_to_migrate = []
    
    for filepath in skills_dir.glob("*_Ab*.py"):
        parsed = parse_skill_filename(filepath.name)
        
        if parsed:
            files_to_migrate.append({
                'path': filepath,
                'skill_id': parsed['skill_id'],
                'model': parsed['model'],
                'ablation_id': parsed['ablation_id']
            })
    
    return files_to_migrate

def main():
    parser = argparse.ArgumentParser(description='遷移現有檔案到新的 experiments 結構')
    parser.add_argument('--dry-run', action='store_true', help='只預覽不執行')
    parser.add_argument('--backup', action='store_true', help='備份原始檔案到 skills/backup/')
    
    args = parser.parse_args()
    
    print(f"\n{'='*80}")
    print(f"🔍 掃描 skills/ 目錄...")
    print(f"{'='*80}\n")
    
    files_to_migrate = scan_skills_directory()
    
    if not files_to_migrate:
        print("❌ 未找到需要遷移的檔案")
        return
    
    # 按 skill_id 和 ablation_id 分組
    grouped = {}
    for file_info in files_to_migrate:
        key = (file_info['skill_id'], file_info['ablation_id'])
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(file_info)
    
    print(f"📊 找到 {len(files_to_migrate)} 個檔案需要遷移")
    print(f"涵蓋 {len(grouped)} 個 (技能, Ablation) 組合\n")
    
    if args.dry_run:
        print("🔍 預覽模式（不會實際修改檔案）\n")
    
    # 執行遷移
    for (skill_id, ablation_id), files in sorted(grouped.items()):
        ablation_name = {1: "Ab1", 2: "Ab2", 3: "Ab3"}[ablation_id]
        
        print(f"\n📁 {skill_id} / {ablation_name}")
        print("-" * 40)
        
        for i, file_info in enumerate(files, 1):
            migrate_file(
                file_info['path'],
                skill_id,
                ablation_id,
                i,
                dry_run=args.dry_run
            )
    
    if not args.dry_run:
        print(f"\n{'='*80}")
        print(f"✅ 遷移完成！")
        print(f"{'='*80}")
        
        if args.backup:
            print("\n📦 備份原始檔案...")
            backup_dir = Path("skills/backup_migrated")
            backup_dir.mkdir(exist_ok=True)
            
            for file_info in files_to_migrate:
                shutil.copy2(file_info['path'], backup_dir / file_info['path'].name)
            
            print(f"✅ 已備份到: {backup_dir}/")
        
        print("\n💡 提示:")
        print("   - 遷移後的檔案位於: experiments/results/{skill_id}/Ab{n}/")
        print("   - 可使用 --backup 選項備份原始檔案")
        print("   - 建議檢查遷移結果後再刪除原始檔案\n")
    else:
        print(f"\n{'='*80}")
        print(f"🔍 預覽完成（未實際執行）")
        print(f"{'='*80}")
        print(f"\n💡 執行遷移請移除 --dry-run 參數\n")

if __name__ == '__main__':
    main()
