"""
分析實驗結果的科學價值 (從資料庫讀取)
"""
import sqlite3
import pandas as pd

conn = sqlite3.connect('instance/kumon_math.db')  # [Fix] 正確的資料庫名稱

# 查詢統計數據
query = """
SELECT 
    skill_id,
    ablation_id,
    COUNT(*) as total_samples,
    SUM(is_crash) as crash_count,
    SUM(is_logic_correct) as correct_count,
    AVG(duration_seconds) as avg_duration,
    AVG(score_complexity) as avg_complexity
FROM execution_samples 
GROUP BY skill_id, ablation_id 
ORDER BY skill_id, ablation_id
"""

df = pd.read_sql_query(query, conn)

# 計算成功率
df['success_rate'] = (df['correct_count'] / df['total_samples'] * 100).round(1)
df['crash_rate'] = (df['crash_count'] / df['total_samples'] * 100).round(1)

print("\n" + "="*100)
print("🔬 實驗結果統計分析 (Ablation Study)")
print("="*100)
print(df.to_string(index=False))

# 提取模型類型（從 skill_id 中）
df['model'] = df['skill_id'].str.extract(r'_(Cloud|14B|7B)_')
df['ablation'] = df['ablation_id'].map({1: 'Ab1-Bare', 2: 'Ab2-Engineered', 3: 'Ab3-FullHealing'})

print("\n" + "="*100)
print("📊 按模型和 Ablation 分組統計")
print("="*100)

pivot = df.pivot_table(
    values='success_rate',
    index='model',
    columns='ablation',
    aggfunc='mean'
)
print(pivot)

print("\n" + "="*100)
print("⏱️  平均執行時間對比 (秒)")
print("="*100)

pivot_time = df.pivot_table(
    values='avg_duration',
    index='model',
    columns='ablation',
    aggfunc='mean'
)
print(pivot_time.round(2))

# 科學價值分析
print("\n" + "="*100)
print("🎯 科學價值分析")
print("="*100)

# 1. Healer 效果分析
if len(df[df['ablation'] == 'Ab2-Engineered']) > 0 and len(df[df['ablation'] == 'Ab3-FullHealing']) > 0:
    ab2_success = df[df['ablation'] == 'Ab2-Engineered']['success_rate'].mean()
    ab3_success = df[df['ablation'] == 'Ab3-FullHealing']['success_rate'].mean()
    healer_improvement = ab3_success - ab2_success
    
    print(f"\n1️⃣  Healer 效果 (Ab3 vs Ab2):")
    print(f"   Ab2 (Engineered-Only):  {ab2_success:.1f}%")
    print(f"   Ab3 (Full Healing):     {ab3_success:.1f}%")
    print(f"   Healer 提升:            +{healer_improvement:.1f}%")
    
    if healer_improvement > 10:
        print(f"   ✅ 科學價值: HIGH - Healer 顯著提升代碼品質")
    elif healer_improvement > 5:
        print(f"   ⚠️  科學價值: MEDIUM - Healer 有一定效果")
    else:
        print(f"   ❌ 科學價值: LOW - Healer 效果不明顯")

# 2. Prompt Engineering 效果分析
if len(df[df['ablation'] == 'Ab1-Bare']) > 0 and len(df[df['ablation'] == 'Ab2-Engineered']) > 0:
    ab1_success = df[df['ablation'] == 'Ab1-Bare']['success_rate'].mean()
    ab2_success = df[df['ablation'] == 'Ab2-Engineered']['success_rate'].mean()
    prompt_improvement = ab2_success - ab1_success
    
    print(f"\n2️⃣  Prompt Engineering 效果 (Ab2 vs Ab1):")
    print(f"   Ab1 (Bare):             {ab1_success:.1f}%")
    print(f"   Ab2 (Engineered):       {ab2_success:.1f}%")
    print(f"   Prompt 提升:            +{prompt_improvement:.1f}%")
    
    if prompt_improvement > 15:
        print(f"   ✅ 科學價值: HIGH - Prompt 工程化顯著提升效能")
    elif prompt_improvement > 10:
        print(f"   ⚠️  科學價值: MEDIUM - Prompt 工程化有明顯效果")
    else:
        print(f"   ❌ 科學價值: LOW - Prompt 工程化效果有限")

# 3. Cloud vs 14B 對比
if '14B' in df['model'].values and 'Cloud' in df['model'].values:
    cloud_ab3 = df[(df['model'] == 'Cloud') & (df['ablation'] == 'Ab3-FullHealing')]['success_rate'].mean()
    local_ab3 = df[(df['model'] == '14B') & (df['ablation'] == 'Ab3-FullHealing')]['success_rate'].mean()
    gap = cloud_ab3 - local_ab3
    
    print(f"\n3️⃣  模型能力對比 (Full Healing 模式):")
    print(f"   Cloud (Gemini):         {cloud_ab3:.1f}%")
    print(f"   Local 14B (Qwen):       {local_ab3:.1f}%")
    print(f"   能力差距:               {gap:.1f}%")
    
    if abs(gap) < 5:
        print(f"   ✅ 科學價值: HIGH - 14B 達到 Cloud 水準，證明系統有效縮小差距")
    elif abs(gap) < 15:
        print(f"   ⚠️  科學價值: MEDIUM - 14B 接近 Cloud，仍有改進空間")
    else:
        print(f"   ❌ 科學價值: LOW - 14B 與 Cloud 差距過大")

# 4. 樣本數檢查
print(f"\n4️⃣  實驗嚴謹性:")
samples_per_group = df.groupby(['model', 'ablation'])['total_samples'].sum()
min_samples = samples_per_group.min()
max_samples = samples_per_group.max()

print(f"   最小樣本數: {min_samples}")
print(f"   最大樣本數: {max_samples}")

if min_samples >= 20:
    print(f"   ✅ 樣本數充足 (≥20)，結果具統計意義")
elif min_samples >= 10:
    print(f"   ⚠️  樣本數偏少 (10-19)，建議增加採樣")
else:
    print(f"   ❌ 樣本數不足 (<10)，結果不具統計意義")

print("\n" + "="*100)
print("📝 總結建議")
print("="*100)
print("""
科學價值評估標準：
1. Healer 提升 >10% → 證明自動修復機制有效
2. Prompt 提升 >15% → 證明工程化設計重要性
3. 14B vs Cloud 差距 <5% → 證明系統成功縮小模型能力差距
4. 樣本數 ≥20 → 確保統計顯著性

如果滿足 3/4 以上條件，本研究具備發表價值（科展/期刊）。
""")

conn.close()
