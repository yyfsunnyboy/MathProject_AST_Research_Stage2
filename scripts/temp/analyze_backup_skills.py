#!/usr/bin/env python3
"""
分析 backup_20260129 中剛剛生成的國中技能
評估複雜度、代碼品質、對應資料庫例題數
找出「最值得精選」的 20 個技能
"""
import os
from pathlib import Path
from collections import defaultdict
import sqlite3

BACKUP_DIR = Path("skills/backup_20260129")
DB_PATH = Path("instance/kumon_math.db")

def analyze_skill_file(filepath):
    """分析單個技能文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return None
    
    # 基本統計
    lines = len(content.split('\n'))
    
    # 檢查特性
    has_multiple_cases = 'random.choice' in content
    has_formatting = 'format' in content.lower()
    has_fractions = 'Fraction' in content
    has_complex_logic = len(content) > 300
    num_helpers = content.count('def ') - 1  # 減去 generate 函數
    
    # 複雜度評分
    complexity = 1
    if lines > 300:
        complexity = 3
    elif lines > 150:
        complexity = 2
    
    if has_fractions or num_helpers > 5:
        complexity = max(complexity, 2)
    
    return {
        'filename': filepath.stem,
        'lines': lines,
        'complexity': complexity,
        'helpers': num_helpers,
        'has_fractions': has_fractions,
        'has_multiple_cases': has_multiple_cases,
    }

def get_db_examples_count(skill_id):
    """查詢資料庫中該技能的例題數"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM textbook_examples WHERE skill_id = ?', (skill_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def main():
    print("🔍 分析 backup_20260129 中的國中技能\n")
    
    # 掃描所有文件
    skills = []
    for filepath in sorted(BACKUP_DIR.glob('jh_*.py')):
        analysis = analyze_skill_file(filepath)
        if analysis:
            # 轉換文件名為 skill_id
            skill_id = 'jh_' + filepath.stem.replace('jh_', '', 1)
            
            # 查詢資料庫例題數
            db_count = get_db_examples_count(skill_id)
            
            analysis['skill_id'] = skill_id
            analysis['db_examples'] = db_count
            skills.append(analysis)
    
    print(f"📊 總共分析 {len(skills)} 個技能\n")
    
    # 按複雜度和品質排序
    print("=" * 100)
    print("【按複雜度分類 - 最值得推薦的】")
    print("=" * 100)
    
    by_complexity = defaultdict(list)
    for skill in skills:
        by_complexity[skill['complexity']].append(skill)
    
    # 依複雜度輸出
    for complexity in sorted(by_complexity.keys(), reverse=True):
        skills_in_comp = by_complexity[complexity]
        comp_name = {1: '簡單', 2: '中等', 3: '複雜'}[complexity]
        
        print(f"\n【{comp_name}（複雜度 {complexity}）】({len(skills_in_comp)} 個)")
        print("-" * 100)
        
        # 排序：優先有資料庫例題 + 複雜度 + 代碼行數
        sorted_skills = sorted(
            skills_in_comp,
            key=lambda x: (-x['db_examples'], -x['lines'], -x['helpers']),
            reverse=False
        )
        
        for i, skill in enumerate(sorted_skills[:15], 1):  # 只顯示前15個
            star = "⭐" if skill['db_examples'] > 5 else ""
            print(f"{i}. {skill['skill_id']}")
            print(f"   行數: {skill['lines']} | 例題: {skill['db_examples']} | 助手函數: {skill['helpers']} {star}")
    
    # 推薦策略
    print("\n" + "=" * 100)
    print("【推薦的 20 支技能（基於現狀）】")
    print("=" * 100)
    
    # 策略：
    # 1. 先選複雜度 3 的（最有說服力）
    # 2. 再選複雜度 2 的（穩定性好）
    # 3. 確保每個都有資料庫例題
    
    recommended = []
    
    # 複雜度 3 優先
    complex_skills = sorted(
        by_complexity[3],
        key=lambda x: (-x['db_examples'], -x['lines']),
    )
    
    # 複雜度 2
    medium_skills = sorted(
        by_complexity[2],
        key=lambda x: (-x['db_examples'], -x['lines']),
    )
    
    # 複雜度 1
    simple_skills = sorted(
        by_complexity[1],
        key=lambda x: (-x['db_examples'], -x['lines']),
    )
    
    # 組合策略：複雜度 3 (8-10) + 複雜度 2 (8-10) + 複雜度 1 (0-4)
    
    print(f"\n複雜度 3: {len(complex_skills)} 個")
    print(f"複雜度 2: {len(medium_skills)} 個")
    print(f"複雜度 1: {len(simple_skills)} 個")
    
    # 選擇邏輯
    print("\n" + "-" * 100)
    print("【推薦組成】")
    print("-" * 100)
    
    # 取複雜度 3 的前 9 個
    recommended_3 = complex_skills[:9]
    print(f"\n✓ 複雜度 3（9個 - 最吸睛）:")
    for i, skill in enumerate(recommended_3, 1):
        print(f"  {i}. {skill['skill_id']}: {skill['lines']}行, {skill['db_examples']}個例題")
    
    # 取複雜度 2 的前 9 個
    recommended_2 = medium_skills[:9]
    print(f"\n✓ 複雜度 2（9個 - 穩定）:")
    for i, skill in enumerate(recommended_2, 1):
        print(f"  {i}. {skill['skill_id']}: {skill['lines']}行, {skill['db_examples']}個例題")
    
    # 取複雜度 1 的前 2 個（已驗證的基石）
    recommended_1 = [s for s in simple_skills if s['db_examples'] > 0][:2]
    print(f"\n✓ 複雜度 1（2個 - 基石）:")
    for i, skill in enumerate(recommended_1, 1):
        print(f"  {i}. {skill['skill_id']}: {skill['lines']}行, {skill['db_examples']}個例題")
    
    total_recommended = recommended_3 + recommended_2 + recommended_1
    
    print(f"\n\n【最終選擇 {len(total_recommended)} 個技能】")
    print("=" * 100)
    
    # 按技能類別分組輸出最終列表
    domains = defaultdict(list)
    
    for skill in total_recommended:
        # 簡單分類
        name = skill['skill_id']
        if '加' in name or '減' in name or '乘' in name or '除' in name or '四則' in name or 'Integer' in name or 'Fraction' in name:
            domain = 'arithmetic'
        elif '方程' in name or 'Equation' in name or 'Expression' in name or 'Linear' in name:
            domain = 'algebra'
        elif '三角' in name or 'Triangle' in name or 'Angle' in name or 'Polygon' in name or 'Geometry' in name:
            domain = 'geometry'
        elif '數列' in name or 'Sequence' in name or 'Series' in name:
            domain = 'sequences'
        elif '統計' in name or 'Mean' in name or 'Chart' in name or 'Distribution' in name or 'Frequency' in name:
            domain = 'statistics'
        elif '機率' in name or 'Proportion' in name:
            domain = 'probability'
        else:
            domain = 'other'
        
        domains[domain].append(skill)
    
    for domain in sorted(domains.keys()):
        print(f"\n【{domain.upper()}】({len(domains[domain])} 個)")
        for i, skill in enumerate(domains[domain], 1):
            print(f"  {i}. {skill['skill_id']}")

if __name__ == "__main__":
    main()
