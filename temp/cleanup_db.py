#!/usr/bin/env python
import sqlite3

conn = sqlite3.connect('instance/kumon_math.db')
cursor = conn.cursor()
cursor.execute("DELETE FROM execution_samples WHERE skill_id LIKE '%ApplicationsOfDerivatives%'")
conn.commit()
conn.close()
print("✅ 資料庫已清空")
