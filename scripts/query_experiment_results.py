# -*- coding: utf-8 -*-
"""
=============================================================================
檔案名稱 (File Name): query_experiment_results.py
功能說明 (Description): 查詢與分析 MCRI V4.2 實驗結果
執行語法 (Usage): python scripts/query_experiment_results.py [--ablation 3] [--skill gh_ApplicationsOfDerivatives]
版本資訊 (Version): V1.0
更新日期 (Date): 2026-02-02
維護團隊 (Maintainer): Math AI Project Team
=============================================================================
"""

import os
import sys
import argparse
from pathlib import Path
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from tabulate import tabulate

# 添加父目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import ExperimentRun, EvaluationItem


def query_summary(session, ablation_id=None, skill_name=None):
    """查詢實驗摘要統計"""
    print("\n" + "="*80)
    print("📊 MCRI V4.2 實驗結果摘要")
    print("="*80)
    
    # 建立查詢
    query = session.query(
        ExperimentRun.ablation_id,
        func.count(ExperimentRun.run_id).label('total_runs'),
        func.avg(ExperimentRun.avg_mcri_total).label('avg_mcri'),
        func.min(ExperimentRun.avg_mcri_total).label('min_mcri'),
        func.max(ExperimentRun.avg_mcri_total).label('max_mcri'),
        func.avg(ExperimentRun.pass_rate).label('avg_pass_rate'),
        func.avg(ExperimentRun.score_l1_total).label('avg_l1'),
        func.avg(ExperimentRun.score_l2_total).label('avg_l2'),
        func.avg(ExperimentRun.avg_l3_total).label('avg_l3'),
        func.avg(ExperimentRun.avg_l4_total).label('avg_l4')
    )
    
    # 篩選條件
    if ablation_id:
        query = query.filter(ExperimentRun.ablation_id == ablation_id)
    if skill_name:
        query = query.filter(ExperimentRun.skill_name == skill_name)
    
    stats = query.group_by(ExperimentRun.ablation_id).all()
    
    if not stats:
        print("⚠️ 沒有找到符合條件的實驗記錄")
        return
    
    # 格式化輸出
    ablation_names = {1: 'Ab1 (Bare)', 2: 'Ab2 (Eng)', 3: 'Ab3 (Healer)'}
    
    headers = ['配置', '實驗次數', '平均MCRI', '最低', '最高', '通過率', 'L1', 'L2', 'L3', 'L4']
    rows = []
    
    for stat in stats:
        ab_name = ablation_names.get(stat.ablation_id, f'Ab{stat.ablation_id}')
        rows.append([
            ab_name,
            stat.total_runs,
            f"{stat.avg_mcri:.1f}" if stat.avg_mcri else 'N/A',
            f"{stat.min_mcri:.1f}" if stat.min_mcri else 'N/A',
            f"{stat.max_mcri:.1f}" if stat.max_mcri else 'N/A',
            f"{stat.avg_pass_rate*100:.1f}%" if stat.avg_pass_rate else 'N/A',
            f"{stat.avg_l1:.1f}" if stat.avg_l1 else 'N/A',
            f"{stat.avg_l2:.1f}" if stat.avg_l2 else 'N/A',
            f"{stat.avg_l3:.1f}" if stat.avg_l3 else 'N/A',
            f"{stat.avg_l4:.1f}" if stat.avg_l4 else 'N/A'
        ])
    
    print(tabulate(rows, headers=headers, tablefmt='grid'))


def query_failure_modes(session, ablation_id=None):
    """查詢失敗模式統計"""
    print("\n" + "="*80)
    print("🔍 失敗模式分析")
    print("="*80)
    
    # 建立查詢
    query = session.query(
        ExperimentRun.ablation_id,
        ExperimentRun.skill_name,
        func.count(EvaluationItem.item_id).label('total_items'),
        func.sum(func.case((EvaluationItem.status == 'Fail', 1), else_=0)).label('syntax_errors'),
        func.sum(func.case((EvaluationItem.status == 'Timeout', 1), else_=0)).label('timeouts'),
        func.sum(func.case((EvaluationItem.status == 'Success', 1), else_=0)).label('successes')
    ).join(EvaluationItem, ExperimentRun.run_id == EvaluationItem.run_id)
    
    if ablation_id:
        query = query.filter(ExperimentRun.ablation_id == ablation_id)
    
    stats = query.group_by(ExperimentRun.ablation_id, ExperimentRun.skill_name).all()
    
    if not stats:
        print("⚠️ 沒有找到評估項目記錄")
        return
    
    ablation_names = {1: 'Ab1 (Bare)', 2: 'Ab2 (Eng)', 3: 'Ab3 (Healer)'}
    
    headers = ['配置', '技能', '總次數', '語法錯誤', 'Timeout', '成功', '成功率']
    rows = []
    
    for stat in stats:
        ab_name = ablation_names.get(stat.ablation_id, f'Ab{stat.ablation_id}')
        success_rate = (stat.successes / stat.total_items * 100) if stat.total_items > 0 else 0
        rows.append([
            ab_name,
            stat.skill_name[:30] + '...' if len(stat.skill_name) > 30 else stat.skill_name,
            stat.total_items,
            stat.syntax_errors,
            stat.timeouts,
            stat.successes,
            f"{success_rate:.1f}%"
        ])
    
    print(tabulate(rows, headers=headers, tablefmt='grid'))


def query_top_runs(session, limit=10, order_by='mcri'):
    """查詢最佳/最差實驗"""
    print("\n" + "="*80)
    print(f"🏆 {'最佳' if order_by == 'mcri' else '最差'} {limit} 次實驗")
    print("="*80)
    
    if order_by == 'mcri':
        runs = session.query(ExperimentRun).order_by(ExperimentRun.avg_mcri_total.desc()).limit(limit).all()
    else:
        runs = session.query(ExperimentRun).order_by(ExperimentRun.avg_mcri_total).limit(limit).all()
    
    if not runs:
        print("⚠️ 沒有找到實驗記錄")
        return
    
    ablation_names = {1: 'Ab1', 2: 'Ab2', 3: 'Ab3'}
    
    headers = ['配置', '技能', '樣本#', 'MCRI', 'L1', 'L2', 'L3', 'L4', '通過率', '時間']
    rows = []
    
    for run in runs:
        ab_name = ablation_names.get(run.ablation_id, f'Ab{run.ablation_id}')
        rows.append([
            ab_name,
            run.skill_name[:25] + '...' if len(run.skill_name) > 25 else run.skill_name,
            run.sample_index,
            f"{run.avg_mcri_total:.1f}" if run.avg_mcri_total else 'N/A',
            run.score_l1_total if run.score_l1_total is not None else 'N/A',
            run.score_l2_total if run.score_l2_total is not None else 'N/A',
            f"{run.avg_l3_total:.1f}" if run.avg_l3_total else 'N/A',
            f"{run.avg_l4_total:.1f}" if run.avg_l4_total else 'N/A',
            f"{run.pass_rate*100:.0f}%" if run.pass_rate else 'N/A',
            run.timestamp.strftime('%m-%d %H:%M') if run.timestamp else 'N/A'
        ])
    
    print(tabulate(rows, headers=headers, tablefmt='grid'))


def query_skill_comparison(session, skill_name):
    """比較同一技能的三個配置"""
    print("\n" + "="*80)
    print(f"📈 技能比較：{skill_name}")
    print("="*80)
    
    stats = session.query(
        ExperimentRun.ablation_id,
        func.count(ExperimentRun.run_id).label('runs'),
        func.avg(ExperimentRun.avg_mcri_total).label('avg_mcri'),
        func.avg(ExperimentRun.score_l1_total).label('avg_l1'),
        func.avg(ExperimentRun.score_l2_total).label('avg_l2'),
        func.avg(ExperimentRun.avg_l3_total).label('avg_l3'),
        func.avg(ExperimentRun.avg_l4_total).label('avg_l4'),
        func.avg(ExperimentRun.pass_rate).label('avg_pass')
    ).filter(ExperimentRun.skill_name == skill_name).group_by(ExperimentRun.ablation_id).all()
    
    if not stats:
        print(f"⚠️ 沒有找到技能 {skill_name} 的實驗記錄")
        return
    
    ablation_names = {1: 'Ab1 (Bare)', 2: 'Ab2 (Eng)', 3: 'Ab3 (Healer)'}
    
    headers = ['配置', '實驗次數', '平均MCRI', 'L1', 'L2', 'L3', 'L4', '通過率']
    rows = []
    
    for stat in stats:
        ab_name = ablation_names.get(stat.ablation_id, f'Ab{stat.ablation_id}')
        rows.append([
            ab_name,
            stat.runs,
            f"{stat.avg_mcri:.1f}" if stat.avg_mcri else 'N/A',
            f"{stat.avg_l1:.1f}" if stat.avg_l1 else 'N/A',
            f"{stat.avg_l2:.1f}" if stat.avg_l2 else 'N/A',
            f"{stat.avg_l3:.1f}" if stat.avg_l3 else 'N/A',
            f"{stat.avg_l4:.1f}" if stat.avg_l4 else 'N/A',
            f"{stat.avg_pass*100:.1f}%" if stat.avg_pass else 'N/A'
        ])
    
    print(tabulate(rows, headers=headers, tablefmt='grid'))


def main():
    parser = argparse.ArgumentParser(description='查詢 MCRI V4.2 實驗結果')
    parser.add_argument('--db-path', default='instance/math_education.db', help='資料庫路徑')
    parser.add_argument('--ablation', type=int, choices=[1, 2, 3], help='篩選配置（1/2/3）')
    parser.add_argument('--skill', help='篩選技能名稱')
    parser.add_argument('--top', type=int, default=10, help='顯示前 N 筆最佳實驗')
    parser.add_argument('--worst', type=int, help='顯示前 N 筆最差實驗')
    parser.add_argument('--compare-skill', help='比較同一技能的三個配置')
    
    args = parser.parse_args()
    
    # 建立資料庫連線
    engine = create_engine(f'sqlite:///{args.db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 總覽統計
        query_summary(session, ablation_id=args.ablation, skill_name=args.skill)
        
        # 失敗模式
        if not args.skill:  # 只有在沒有指定技能時才顯示失敗模式（避免重複）
            query_failure_modes(session, ablation_id=args.ablation)
        
        # 最佳實驗
        if args.top:
            query_top_runs(session, limit=args.top, order_by='mcri')
        
        # 最差實驗
        if args.worst:
            query_top_runs(session, limit=args.worst, order_by='worst')
        
        # 技能比較
        if args.compare_skill:
            query_skill_comparison(session, args.compare_skill)
        
    finally:
        session.close()


if __name__ == '__main__':
    main()
