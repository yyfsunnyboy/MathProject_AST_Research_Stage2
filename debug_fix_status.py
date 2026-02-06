#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug script to trace regex_fixes and ast_fixes values"""
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

# Set VERBOSE_LEVEL to see DEBUG output
import config
config.VERBOSE_LEVEL = 2

# Import the code generator
from core.code_generator import auto_generate_skill_code

print("=" * 80)
print("DEBUG: Testing code generation with VERBOSE_LEVEL=2")
print("=" * 80)

# Generate a skill code with Ab3 (Full Healing)
skill_id = "ApplicationsOfDerivatives"
ablation_id = 3
model_size_class = "14b"

print(f"\nGenerating: {skill_id} with Ab{ablation_id}")
print(f"Model: {model_size_class}")
print("-" * 80)

try:
    result = auto_generate_skill_code(
        skill_id=skill_id,
        ablation_id=ablation_id,
        model_size_class=model_size_class
    )
    
    print("\n" + "=" * 80)
    print("✅ Generation completed successfully")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ Error during generation: {type(e).__name__}")
    print(f"   {str(e)[:200]}")
    import traceback
    traceback.print_exc()
