
import sqlite3
import os

def inspect_db(db_path):
    print(f"\n🔍 Inspecting: {db_path}")
    if not os.path.exists(db_path):
        print("❌ File not found!")
        return
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("⚠️ No tables found in DB.")
        else:
            print(f"Found {len(tables)} tables: {[t[0] for t in tables]}")
            
            for table_name in [t[0] for t in tables]:
                print(f"\n--- Table: {table_name} ---")
                # Count rows
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"Row Count: {count}")
                # Skip printing rows to avoid clutter/truncation


        conn.close()
    except Exception as e:
        print(f"❌ Error reading DB: {e}")

if __name__ == "__main__":
    db_files = [
        r"E:\Python\MathProject_AST_Research\instance\benchmark_20260220_000857.db",
        r"E:\Python\MathProject_AST_Research\instance\benchmark_20260220_084756.db"
    ]
    
    for f in db_files:
        inspect_db(f)
