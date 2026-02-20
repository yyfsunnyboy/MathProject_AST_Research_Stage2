
import pandas as pd
import numpy as np
import scipy.stats as stats
import os

def regenerate_summary():
    runs_path = r"E:\Python\MathProject_AST_Research\agent_tools\reports\jh_數學2上_FourOperationsOfRadicals\jh_數學2上_FourOperationsOfRadicals_runs_20260220_000857.csv"
    summary_path = r"E:\Python\MathProject_AST_Research\agent_tools\reports\jh_數學2上_FourOperationsOfRadicals\jh_數學2上_FourOperationsOfRadicals_summary_20260220_000857.csv"
    
    print(f"Reading runs from: {runs_path}")
    df = pd.read_csv(runs_path)
    
    # 1. Group by Model, Skill, Ablation
    grouped = df.groupby(['model_name', 'skill_name', 'ablation_id'])
    
    summary_rows = []
    
    for (model, skill, ab_id), group in grouped:
        print(f"Processing: {model} - {skill} - Ab{ab_id} (n={len(group)})")
        
        # Determine success runs for metrics
        # For average scores, we only include successful runs?
        # Typically MCRI score of 0 for failed runs is included in 'pass_rate' calc but maybe not in 'avg_mcri_total'?
        # In current design, failed runs have avg_mcri_total=0. So including them lowers the average significantly.
        # Let's align with evaluate_mcri logic: compute on ALL runs.
        
        # sample_count: unique sample_index
        sample_count = group['sample_index'].nunique()
        total_runs = len(group)
        
        # Metrics
        mean_mcri = group['avg_mcri_total'].mean()
        std_mcri = group['avg_mcri_total'].std()
        
        if total_runs > 1:
            sem = std_mcri / np.sqrt(total_runs)
            ci95_lower = mean_mcri - 1.96 * sem
            ci95_upper = mean_mcri + 1.96 * sem
        else:
            ci95_lower = np.nan
            ci95_upper = np.nan
            
        mean_l3_ext = group['avg_l3_2_external'].mean()
        mean_l4_num = group['avg_l4_1_numeric'].mean()
        mean_prog = group['score_program_total'].mean()
        mean_math = group['score_math_total'].mean()
        mean_l5 = group['score_l5_architecture'].mean()
        mean_l4_mqi = group['avg_l4_4_mqi'].mean()
        
        # P-Value vs Ab1 (of same model/skill)
        p_val = ""
        notes = "-"
        
        if ab_id != 1:
            # Find Ab1 group
            ab1_group = df[(df['model_name'] == model) & (df['skill_name'] == skill) & (df['ablation_id'] == 1)]
            if not ab1_group.empty and len(ab1_group) > 1 and len(group) > 1:
                 t_stat, p = stats.ttest_ind(group['avg_mcri_total'], ab1_group['avg_mcri_total'], equal_var=False)
                 p_val = p
                 if p < 0.001:
                     notes = f"Ab{ab_id} vs Ab1: p<0.001 (Highly Significant)"
                 elif p < 0.05:
                     notes = f"Ab{ab_id} vs Ab1: p={p:.4f} (Significant)"
                 else:
                     notes = f"Ab{ab_id} vs Ab1: p={p:.4f} (Not Significant)"
        
        row = {
            'summary_id': f"{model}_{skill}_ab{ab_id}", # Simplified ID
            'skill_name': skill,
            'ablation_id': ab_id,
            'model_name': model,
            'sample_count': sample_count,
            'total_runs': total_runs,
            'mean_mcri_total': round(mean_mcri, 2),
            'std_mcri_total': round(std_mcri, 2),
            'ci95_lower': round(ci95_lower, 2),
            'ci95_upper': round(ci95_upper, 2),
            'mean_l3_external': round(mean_l3_ext, 2),
            'mean_l4_numeric': round(mean_l4_num, 2),
            'mean_program_total': round(mean_prog, 2),
            'mean_math_total': round(mean_math, 2),
            'mean_l5_architecture': round(mean_l5, 2),
            'mean_l4_mqi': round(mean_l4_mqi, 2),
            'p_value_vs_ab1': p_val,
            'notes': notes
        }
        summary_rows.append(row)
        
    # Create DataFrame
    summary_df = pd.DataFrame(summary_rows)
    
    # Sort
    summary_df = summary_df.sort_values(by=['model_name', 'ablation_id'])
    
    # Write
    print(f"Writing summary to: {summary_path}")
    summary_df.to_csv(summary_path, index=False)
    print("Done.")

if __name__ == "__main__":
    regenerate_summary()
