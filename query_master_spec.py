#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询 MASTER_SPEC 提示词内容和比较分析
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path

def query_master_spec():
    db_path = Path("instance/kumon_math.db")
    
    if not db_path.exists():
        print(f"❌ 数据库文件不存在: {db_path.absolute()}")
        return
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 查询 skill_gencode_prompt 表中的 MASTER_SPEC 记录
    query = """
    SELECT 
        id,
        skill_id,
        prompt_type,
        prompt_content,
        created_at,
        creation_total_tokens
    FROM skill_gencode_prompt
    WHERE skill_id = 'gh_ApplicationsOfDerivatives' 
      AND prompt_type = 'MASTER_SPEC'
    ORDER BY created_at DESC
    """
    
    print("=" * 100)
    print("查询: skill_gencode_prompt 表")
    print(f"条件: skill_id='gh_ApplicationsOfDerivatives' AND prompt_type='MASTER_SPEC'")
    print("=" * 100)
    print()
    
    cursor.execute(query)
    records = cursor.fetchall()
    
    if not records:
        print("⚠️  未找到记录")
        conn.close()
        return
    
    print(f"✅ 找到 {len(records)} 条记录\n")
    
    # 详细显示每条记录
    for idx, record in enumerate(records, 1):
        print(f"记录 #{idx}")
        print("-" * 100)
        print(f"ID: {record['id']}")
        print(f"Skill ID: {record['skill_id']}")
        print(f"Prompt Type: {record['prompt_type']}")
        print(f"Created At: {record['created_at']}")
        print(f"Token Count: {record['creation_total_tokens']}")
        
        content = record['prompt_content']
        if content:
            content_len = len(content)
            print(f"内容长度: {content_len} 字符")
            print(f"\n内容预览 (前 500 字符):")
            print("-" * 100)
            print(content[:500])
            if len(content) > 500:
                print("\n... (中间省略) ...\n")
                print("内容末尾 (后 200 字符):")
                print(content[-200:])
        else:
            print("内容长度: 0 字符 (空)")
        
        print(f"\n")
    
    # 比较分析
    print("=" * 100)
    print("比较分析")
    print("=" * 100)
    print()
    
    if len(records) >= 2:
        print("多条记录对比:")
        print()
        for idx, record in enumerate(records, 1):
            content = record['prompt_content'] or ""
            token_count = record['creation_total_tokens']
            print(f"记录 #{idx}")
            print(f"  创建时间: {record['created_at']}")
            print(f"  内容字符数: {len(content)}")
            print(f"  Token 数量: {token_count if token_count else '未记录'}")
            print()
        
        # 计算差异
        contents = [r['prompt_content'] or "" for r in records]
        lengths = [len(c) for c in contents]
        
        if len(set(lengths)) > 1:
            print(f"⚠️  内容长度存在差异:")
            print(f"  最长: {max(lengths)} 字符")
            print(f"  最短: {min(lengths)} 字符")
            print(f"  差异: {max(lengths) - min(lengths)} 字符")
            print()
        else:
            print(f"✅ 所有记录内容长度相同: {lengths[0]} 字符")
            print()
        
        # 检查内容是否完全相同
        if len(set(contents)) == 1:
            print("✅ 所有记录的内容完全相同")
        else:
            print("⚠️  内容存在差异，以下是内容哈希对比:")
            import hashlib
            for idx, content in enumerate(contents, 1):
                hash_val = hashlib.sha256(content.encode()).hexdigest()[:16]
                print(f"  记录 #{idx}: {hash_val}")
        
        print()
        
        # Token 分析
        tokens = [r['creation_total_tokens'] for r in records if r['creation_total_tokens']]
        if tokens:
            print(f"Token 统计:")
            print(f"  总 Token: {sum(tokens)}")
            print(f"  平均 Token: {sum(tokens) / len(tokens):.1f}")
            print(f"  最大 Token: {max(tokens)}")
            print(f"  最小 Token: {min(tokens)}")
            if len(set(tokens)) > 1:
                print(f"  Token 差异: {max(tokens) - min(tokens)}")
                print()
                if 680 <= max(tokens) - min(tokens) <= 700:
                    print("⚠️  Token 差异在 680-700 范围内 (接近 687 tokens 的差异)")
    else:
        print(f"仅有 {len(records)} 条记录，无法比较")
    
    conn.close()
    
    print()
    print("=" * 100)

if __name__ == "__main__":
    query_master_spec()
