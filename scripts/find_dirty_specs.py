
import sqlite3
import os

DB_PATH = 'instance/kumon_math.db'

def inspect_db():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"📋 Tables found: {tables}")
    
    # 2. Find likely skill table
    skill_table = None
    if 'skills' in tables: skill_table = 'skills'
    elif 'skill' in tables: skill_table = 'skill'
    
    if not skill_table:
        print("⚠️ No obvious 'skills' table found.")
        # Try inspecting columns of all tables
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            if 'master_spec' in columns:
                skill_table = table
                print(f"✅ Found 'master_spec' in table: {table}")
                break
    
    if not skill_table:
        print("❌ Could not locate table with 'master_spec'.")
        conn.close()
        return

    # 3. Search for dirty specs
    print(f"\n🔍 Searching for dirty specs in table '{skill_table}'...")
    try:
        query = f"SELECT id, master_spec FROM {skill_table} WHERE master_spec LIKE '%Google AI Error%' OR master_spec LIKE '%PERMISSION_DENIED%'"
        cursor.execute(query)
        dirty_rows = cursor.fetchall()
        
        if not dirty_rows:
            print("✅ No dirty specs found! Database is clean.")
        else:
            print(f"🚨 Found {len(dirty_rows)} dirty specs:")
            print("-" * 60)
            for row in dirty_rows:
                skill_id = row[0]
                spec_snippet = row[1][:100].replace('\n', ' ') + "..."
                print(f"🔴 Skill ID: {skill_id}")
                print(f"   Snippet: {spec_snippet}")
            print("-" * 60)
            
            # Optional: Ask user if they want to clean them (set to NULL or empty)
            # For now, just report.
            
    except Exception as e:
        print(f"❌ SQL Error: {e}")

    conn.close()

if __name__ == "__main__":
    inspect_db()
