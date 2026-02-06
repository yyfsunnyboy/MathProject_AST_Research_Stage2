import sqlite3
conn = sqlite3.connect('instance/kumon_math.db')
cursor = conn.cursor()

# 查詢今天的採樣數據
cursor.execute("""
SELECT 
    skill_id,
    ablation_id,
    COUNT(*) as count,
    SUM(is_crash) as crashes,
    SUM(is_logic_correct) as correct,
    MAX(timestamp) as latest
FROM execution_samples 
WHERE skill_id LIKE '%ApplicationsOfDerivatives%'
  AND timestamp >= '2026-01-31'
GROUP BY skill_id, ablation_id 
ORDER BY skill_id, ablation_id
""")

print("\n今日 (2026-01-31) ApplicationsOfDerivatives 採樣結果:")
print("="*120)
print(f"{'Skill_ID':<50} {'Ab':<5} {'Total':<8} {'Crash':<8} {'Correct':<10} {'Success%':<12} {'Latest Time'}")
print("="*120)

for r in cursor.fetchall():
    success_rate = (r[4] / r[2] * 100) if r[2] > 0 else 0
    print(f"{r[0]:<50} {r[1]:<5} {r[2]:<8} {r[3]:<8} {r[4]:<10} {success_rate:>6.1f}%      {r[5]}")

conn.close()
