#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看数据库表结构
"""
import sqlite3
from pathlib import Path

def show_tables():
    db_path = Path("instance/kumon_math.db")
    
    if not db_path.exists():
        print(f"❌ 数据库文件不存在: {db_path.absolute()}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # 查看所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("数据库中的表:")
    print("-" * 50)
    for table in tables:
        print(f"  - {table[0]}")
    
    print("\n" + "=" * 50)
    print("\n查看各表的结构:")
    print("=" * 50)
    
    for table in tables:
        table_name = table[0]
        print(f"\n📋 表名: {table_name}")
        print("-" * 50)
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        for col in columns:
            col_id, col_name, col_type, notnull, dflt_value, pk = col
            print(f"  {col_name:<30} {col_type:<15} (PK: {bool(pk)})")
        
        # 显示表中的记录数
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"\n  记录数: {count}")
    
    conn.close()

if __name__ == "__main__":
    show_tables()
