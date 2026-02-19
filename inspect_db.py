import sqlite3
import pandas as pd

DB_PATH = r"E:\Python\MathProject_AST_Research\instance\benchmark.db"

def check_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Get Table Names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables: {tables}")
        
        # 2. Get Columns for 'benchmark_runs' (assuming this is the table)
        table_name = 'benchmark_results' # Guessing name, will adjust based on step 1 if needed.
        # Let's check the first table found if any
        if tables:
            table_name = tables[0][0]
            print(f"\nScanning table: {table_name}")
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            col_names = [col[1] for col in columns]
            print(f"Columns: {col_names}")
            
            # 3. Check for specific columns
            target_cols = ['latency_ms', 'prompt_tokens', 'completion_tokens', 'total_tokens']
            missing = [c for c in target_cols if c not in col_names]
            if missing:
                print(f"❌ Missing columns: {missing}")
            else:
                print(f"✅ All target columns present.")

            # 4. Check recent data for these columns
            if not missing:
                query = f"SELECT run_id, model_name, latency_ms, prompt_tokens, completion_tokens FROM {table_name} ORDER BY timestamp DESC LIMIT 5"
                try:
                    df = pd.read_sql_query(query, conn)
                    print("\nRecent Data (Top 5):")
                    print(df.to_string())
                except Exception as e:
                    print(f"Error querying data: {e}")
        else:
            print("❌ No tables logic found.")

        conn.close()
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    check_db()
