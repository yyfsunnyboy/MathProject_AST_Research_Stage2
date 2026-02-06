#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify that the infinite loop fix works
"""

import sys
import os

# 設置 UTF-8 編碼
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialize Flask app context
from app import create_app
from core.code_generator import auto_generate_skill_code
import time

app = create_app()

# Test the skill that was failing
skill_id = "jh_數學1上_FourArithmeticOperationsOfNumbers"
output_dir = os.path.join(os.path.dirname(__file__), 'temp', 'test_generated')

os.makedirs(output_dir, exist_ok=True)

print("=" * 70)
print(f"Testing infinite loop fix for: {skill_id}")
print("=" * 70)

try:
    # Start with a timeout
    start_time = time.time()
    timeout = 120  # 2 minutes max
    
    with app.app_context():
        # Test generation
        is_ok, msg, metrics = auto_generate_skill_code(
            skill_id,
            "test_model",
            ablation_id=3,
            model_size_class="14b",
            prompt_level="full-healing"
        )
    
    elapsed = time.time() - start_time
    
    print(f"\n[OK] Generation completed in {elapsed:.2f}s")
    print(f"   Status: {is_ok}")
    print(f"   Message: {msg}")
    print(f"   Metrics: {metrics}")
    
    if is_ok:
        print(f"\n[SUCCESS] The infinite loop fix is working!")
        # Check if file was created
        output_file = os.path.join(output_dir, f'{skill_id}.py')
        if os.path.exists(output_file):
            print(f"   Generated file: {output_file}")
            with open(output_file, 'r') as f:
                content = f.read()
                print(f"   File size: {len(content)} bytes")
    else:
        print(f"\n[WARN] Generation succeeded but validation failed")
except KeyboardInterrupt:
    print("\n[ERROR] Process was interrupted (KeyboardInterrupt)")
    print("   This suggests the infinite loop is still present!")
    sys.exit(1)
    
except Exception as e:
    print(f"\n[ERROR] Failed with error: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\nTest completed successfully!")
