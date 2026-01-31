#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Ab3 regeneration after healer fixes
"""
import sys
import os
sys.path.insert(0, 'e:\\Python\\MathProject_AST_Research')
os.chdir('e:\\Python\\MathProject_AST_Research')

print("="*70)
print("Testing Ab3 Regeneration (Single Skill)")
print("="*70)

# Configure environment
os.environ.setdefault('FLASK_ENV', 'development')

try:
    from core.code_generator import auto_generate_skill_code
    
    skill_config = {
        'skill_id': 1,  # gh_ApplicationsOfDerivatives from your DB
        'ablation_id': 3,
        'regenerate': True
    }
    
    print(f"\n🎯 Generating with config:")
    print(f"   Skill ID: {skill_config['skill_id']}")
    print(f"   Ablation: Ab{skill_config['ablation_id']} (Full Healing + Mojibake Fix)")
    print(f"   Mode: Regenerate = True\n")
    
    result = auto_generate_skill_code(**skill_config)
    
    if result['success']:
        print("\n✅ Generation successful!")
        file_path = result['file_path']
        print(f"   File: {file_path}")
        
        # Verify file
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"   Size: {len(content)} bytes")
            
            # Check for mojibake
            mojibake = any(c in content for c in ['冽', '嚗', '靽', '瑕', '漲', '澆'])
            print(f"   Mojibake: {'❌ FOUND' if mojibake else '✅ None'}")
            
            # Check for undefined functions
            undefined_funcs = ['polynomial_to_string', 'fmt_polynomial']
            for func in undefined_funcs:
                if f'{func}(' in content:
                    # Check if it's defined
                    if f'def {func}(' not in content:
                        print(f"   ❌ Undefined function: {func}()")
                    else:
                        print(f"   ✅ Function defined: {func}()")
            
            # Try compile
            try:
                compile(content, file_path, 'exec')
                print("   ✅ Syntax valid")
            except SyntaxError as e:
                print(f"   ❌ Syntax error: {e}")
        else:
            print(f"   ❌ File not found!")
    else:
        error = result.get('error', 'Unknown error')
        print(f"\n❌ Generation failed: {error}")
        
        # Check for specific errors
        if 'undefined' in str(error).lower() or 'not defined' in str(error).lower():
            print("\n   ⚠️  This is likely the polynomial_to_string undefined error")
            print("   The Healer fix should resolve this in the next run")

except Exception as e:
    import traceback
    print(f"\n❌ Exception: {e}")
    traceback.print_exc()

print("\n" + "="*70)
