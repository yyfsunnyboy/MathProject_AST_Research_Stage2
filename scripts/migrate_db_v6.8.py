import sqlite3
import os

DB_PATH = r"E:\Python\MathProject_AST_Research\instance\benchmark.db"

def migrate_db():
    print(f"Migrating database at: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print("❌ Database not found!")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Columns to add
        new_columns = [
            ("healer_fixes_basic", "INTEGER"),
            ("healer_fixes_regex", "INTEGER"),
            ("healer_fixes_ast", "INTEGER")
        ]
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(experiment_runs)")
        existing_cols = [col[1] for col in cursor.fetchall()]
        
        for col_name, col_type in new_columns:
            if col_name not in existing_cols:
                print(f"Adding column: {col_name} ({col_type})...")
                try:
                    cursor.execute(f"ALTER TABLE experiment_runs ADD COLUMN {col_name} {col_type} DEFAULT 0")
                except Exception as e:
                    print(f"Failed to add {col_name}: {e}")
            else:
                print(f"Column {col_name} already exists.")
        
        conn.commit()
        conn.close()
        print("✅ Migration complete.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate_db()
