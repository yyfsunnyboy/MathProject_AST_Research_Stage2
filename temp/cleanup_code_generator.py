#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理 code_generator.py，移除重複的 PERFECT_UTILS 定義
"""

def cleanup_code_generator():
    file_path = r'e:\Python\MathProject_AST_Research\core\code_generator.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 找到需要刪除的範圍
    # 從 "PERFECT_UTILS = _build_perfect_utils()" 之後的第一個骨架定義
    # 到第二個骨架定義之前
    
    new_lines = []
    skip_mode = False
    found_perfect_utils_call = False
    skeleton_count = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 檢測 PERFECT_UTILS = _build_perfect_utils()
        if 'PERFECT_UTILS = _build_perfect_utils()' in line:
            found_perfect_utils_call = True
            new_lines.append(line)
            i += 1
            continue
        
        # 檢測骨架定義
        if '# 3. 骨架與 Prompt 定義' in line or '# 3. 撉冽' in line:
            skeleton_count += 1
            if skeleton_count == 1 and found_perfect_utils_call:
                # 第一個骨架定義之後開始跳過
                skip_mode = True
            elif skeleton_count == 2:
                # 第二個骨架定義，停止跳過
                skip_mode = False
                skeleton_count = 0  # 重置
        
        # 決定是否保留這一行
        if not skip_mode:
            new_lines.append(line)
        
        i += 1
    
    # 寫回檔案
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"✅ 清理完成！")
    print(f"   原始行數: {len(lines)}")
    print(f"   清理後: {len(new_lines)}")
    print(f"   減少: {len(lines) - len(new_lines)} 行")

if __name__ == '__main__':
    cleanup_code_generator()
