#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Direct test of Ab3 regeneration with mojibake fix
Avoids Flask app initialization to prevent encoding issues
"""

import sys
import os
sys.path.insert(0, 'e:\\Python\\MathProject_AST_Research')
os.chdir('e:\\Python\\MathProject_AST_Research')

# Directly import and test
from core.code_generator import remove_mojibake_comments, auto_generate_skill_code

print("="*60)
print("TEST 1: Mojibake removal function")
print("="*60)

# Test with corrupted code
test_code = """def test():
    # 1. ?冽??? polynomial_degree (2~5) ??num_terms (2~4)??
    x = 1
    # Normal comment
    return x
"""

print("Original code:")
print(test_code)
print("\nRemoving mojibake...")
cleaned = remove_mojibake_comments(test_code)
print("\nCleaned code:")
print(cleaned)

has_mojibake = any(char in test_code for char in ['冽', '嚗', '靽', '瑕', '漲', '澆'])
cleaned_ok = not any(char in cleaned for char in ['冽', '嚗', '靽', '瑕', '漲', '澆'])
code_ok = 'x = 1' in cleaned and 'Normal comment' in cleaned

print(f"\n✅ Mojibake detected: {has_mojibake}")
print(f"✅ Mojibake removed: {cleaned_ok}")
print(f"✅ Code preserved: {code_ok}")

print("\n" + "="*60)
print("TEST 2: Attempt Ab3 regeneration")
print("="*60)

try:
    # Get the skill first
    from models import Skill
    skill = Skill.query.filter_by(gh_skill_id='gh_ApplicationsOfDerivatives_Cloud').first()
    
    if skill:
        print(f"✅ Found skill: {skill.skill_name}")
        print(f"   Skill ID: {skill.id}")
        print(f"   Version: {skill.version}")
        
        print("\nAttempting to regenerate with Ab3 (Gemini)...")
        
        # Call auto_generate_skill_code
        result = auto_generate_skill_code(
            skill_id=skill.id,
            ablation_id=3,  # Ab3 = Gemini
            regenerate=True
        )
        
        if result and result.get('success'):
            print("\n✅ Generation successful!")
            print(f"   File: {result.get('file_path')}")
            
            # Check if file exists
            if os.path.exists(result['file_path']):
                with open(result['file_path'], 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for mojibake
                mojibake_chars = ['冽', '嚗', '靽', '瑕', '漲', '澆']
                has_mojibake = any(char in content for char in mojibake_chars)
                
                print(f"   File size: {len(content)} bytes")
                print(f"   Has mojibake: {has_mojibake}")
                
                if has_mojibake:
                    print("   ⚠️  WARNING: Mojibake still present!")
                    for char in mojibake_chars:
                        if char in content:
                            print(f"      Found: {char}")
                else:
                    print("   ✅ No mojibake detected!")
                
                # Check syntax
                try:
                    compile(content, result['file_path'], 'exec')
                    print("   ✅ Syntax is valid!")
                except SyntaxError as e:
                    print(f"   ❌ Syntax error: {e}")
            else:
                print(f"   ❌ File not found: {result['file_path']}")
        else:
            error_msg = result.get('error', 'Unknown error') if result else 'No result'
            print(f"\n❌ Generation failed: {error_msg}")
            
    else:
        print("❌ Skill 'gh_ApplicationsOfDerivatives_Cloud' not found in database")
        print("\n   Listing available skills...")
        skills = Skill.query.limit(5).all()
        for s in skills:
            print(f"   - {s.gh_skill_id}: {s.skill_name}")

except Exception as e:
    import traceback
    print(f"\n❌ Error: {e}")
    print("\nTraceback:")
    traceback.print_exc()

print("\n" + "="*60)
print("Test complete")
print("="*60)
