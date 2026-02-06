#!/usr/bin/env python3
"""
分析 backup_GenByGemini 中的技能函數
理解品質水準、複雜度、domain 分類
決定如何選擇 20 支拿金牌的技能
"""
import os
import re
from pathlib import Path
from collections import defaultdict

SKILLS_DIR = Path("skills/backup_GenByGemini")

def analyze_skill_file(filepath):
    """分析一個技能文件的複雜度和特性"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return None
    
    # 提取基本信息
    has_generate = 'def generate(' in content
    has_helper_functions = bool(re.findall(r'def \w+\(', content))
    num_helper_functions = len(re.findall(r'^def \w+\(', content, re.MULTILINE))
    
    # 複雜度指標
    lines_of_code = len(content.split('\n'))
    imports = len(re.findall(r'^import |^from ', content, re.MULTILINE))
    
    # 是否包含數學操作
    has_polynomial_ops = 'poly' in content.lower()
    has_integration = 'integral' in content.lower() or 'integrate' in content.lower()
    has_derivative = 'deriv' in content.lower()
    has_matrix = 'matrix' in content.lower()
    has_probability = 'prob' in content.lower()
    has_statistics = 'stat' in content.lower()
    has_trigonometry = 'trig' in content.lower()
    
    # 複雜度評分 (簡單=1, 中等=2, 複雜=3)
    complexity = 1
    if lines_of_code > 300:
        complexity = 3
    elif lines_of_code > 150:
        complexity = 2
    
    if has_polynomial_ops or has_integration or has_derivative:
        complexity = max(complexity, 3)
    elif has_matrix or has_probability:
        complexity = max(complexity, 2)
    
    # 題型分類
    domain = categorize_domain(filepath.stem)
    
    return {
        'filename': filepath.stem,
        'filepath': str(filepath),
        'lines': lines_of_code,
        'imports': imports,
        'num_helpers': num_helper_functions,
        'has_generate': has_generate,
        'complexity': complexity,
        'domain': domain,
        'features': {
            'polynomial': has_polynomial_ops,
            'integration': has_integration,
            'derivative': has_derivative,
            'matrix': has_matrix,
            'probability': has_probability,
            'statistics': has_statistics,
            'trigonometry': has_trigonometry,
        }
    }

def categorize_domain(filename):
    """根據文件名分類 domain"""
    if filename.startswith('gh_'):
        # 高中數學 - 進一步細分
        text = filename[3:].lower()
        
        if any(x in text for x in ['deriv', 'integral', 'calculus']):
            return 'calculus'
        elif any(x in text for x in ['matrix', 'vector', 'determinant', 'transform']):
            return 'linear_algebra'
        elif any(x in text for x in ['prob', 'distribution', 'bayes', 'expected', 'variance']):
            return 'probability_statistics'
        elif any(x in text for x in ['trig', 'sine', 'cosine', 'angle', 'radian']):
            return 'trigonometry'
        elif any(x in text for x in ['circle', 'ellipse', 'parabola', 'hyperbola', 'conic']):
            return 'conic_sections'
        elif any(x in text for x in ['complex', 'polar']):
            return 'complex_numbers'
        elif any(x in text for x in ['sequence', 'series', 'binomial']):
            return 'sequences_series'
        elif any(x in text for x in ['line', 'point', 'plane', 'space', 'distance', 'angle']):
            return 'analytic_geometry'
        elif any(x in text for x in ['function', 'exponential', 'logarithm', 'polynomial']):
            return 'functions'
        elif any(x in text for x in ['equation', 'inequality', 'linear']):
            return 'algebra'
        elif any(x in text for x in ['data', 'regression', 'correlation']):
            return 'data_analysis'
        else:
            return 'other_gh'
    
    elif filename.startswith('jh_'):
        # 國中數學
        return 'junior_high'
    else:
        return 'misc'

def main():
    print("🔍 分析 Gemini 生成的技能函數\n")
    
    # 掃描所有技能文件
    skills = []
    for filepath in sorted(SKILLS_DIR.glob('*.py')):
        if filepath.name == '__init__.py':
            continue
        
        analysis = analyze_skill_file(filepath)
        if analysis:
            skills.append(analysis)
    
    print(f"📊 總共分析 {len(skills)} 個技能\n")
    
    # 按 domain 統計
    by_domain = defaultdict(list)
    by_complexity = defaultdict(list)
    
    for skill in skills:
        by_domain[skill['domain']].append(skill)
        by_complexity[skill['complexity']].append(skill)
    
    print("=" * 100)
    print("【按 Domain 統計】")
    print("=" * 100)
    for domain in sorted(by_domain.keys()):
        skills_in_domain = by_domain[domain]
        print(f"\n{domain}: {len(skills_in_domain)} 個技能")
        
        # 展示複雜度分佈
        complexity_dist = defaultdict(int)
        for s in skills_in_domain:
            complexity_dist[s['complexity']] += 1
        
        dist_str = " | ".join([f"簡(1): {complexity_dist[1]}", 
                               f"中(2): {complexity_dist[2]}", 
                               f"複(3): {complexity_dist[3]}"])
        print(f"  複雜度分佈: {dist_str}")
        
        # 展示前 5 個
        print(f"  範例:")
        for skill in sorted(skills_in_domain, key=lambda x: -x['lines'])[:5]:
            print(f"    - {skill['filename']}: {skill['lines']} 行")
    
    print("\n" + "=" * 100)
    print("【按複雜度統計】")
    print("=" * 100)
    for complexity in sorted(by_complexity.keys()):
        skills_in_comp = by_complexity[complexity]
        comp_name = {1: '簡單', 2: '中等', 3: '複雜'}[complexity]
        print(f"\n{comp_name} ({complexity}): {len(skills_in_comp)} 個技能")
        print(f"  平均行數: {sum(s['lines'] for s in skills_in_comp) // len(skills_in_comp)}")
    
    # 推薦策略
    print("\n" + "=" * 100)
    print("【選擇 20 支技能的策略】")
    print("=" * 100)
    
    # 優先選擇複雜度高 + domain 多樣化的
    recommended = {}
    
    # 策略：每個 domain 選 1-3 個複雜度最高的
    for domain in sorted(by_domain.keys()):
        domain_skills = sorted(by_domain[domain], 
                              key=lambda x: (-x['complexity'], -x['lines']))
        
        # 取前 2-3 個複雜度高的
        if domain == 'calculus':  # calculus 最重要
            count = 3
        elif domain in ['linear_algebra', 'conic_sections', 'trigonometry']:
            count = 2
        else:
            count = 1
        
        recommended[domain] = domain_skills[:count]
    
    total_selected = sum(len(v) for v in recommended.values())
    print(f"\n初步選擇: {total_selected} 個技能")
    
    for domain in sorted(recommended.keys()):
        skills_list = recommended[domain]
        print(f"\n【{domain}】")
        for skill in skills_list:
            print(f"  ✓ {skill['filename']}: {skill['lines']}行, 複雜度{skill['complexity']}")
    
    # 保存詳細分析
    with open('skill_analysis_report.txt', 'w', encoding='utf-8') as f:
        f.write("詳細技能分析報告\n")
        f.write("=" * 100 + "\n\n")
        
        for domain in sorted(by_domain.keys()):
            f.write(f"\n【{domain}】({len(by_domain[domain])}個技能)\n")
            f.write("-" * 100 + "\n")
            
            for skill in sorted(by_domain[domain], key=lambda x: -x['lines'])[:10]:
                f.write(f"\n{skill['filename']}\n")
                f.write(f"  行數: {skill['lines']}\n")
                f.write(f"  複雜度: {skill['complexity']}\n")
                f.write(f"  import數: {skill['imports']}\n")
                f.write(f"  助手函數: {skill['num_helpers']}\n")
                features = [k for k, v in skill['features'].items() if v]
                if features:
                    f.write(f"  特性: {', '.join(features)}\n")
    
    print("\n✅ 詳細分析已保存到 skill_analysis_report.txt")

if __name__ == "__main__":
    main()
