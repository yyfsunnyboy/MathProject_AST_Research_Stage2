#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Ab3 regeneration after healer fixes
"""
import sys
import os
sys.path.insert(0, 'e:\\Python\\MathProject_AST_Research')
os.chdir('e:\\Python\\MathProject_AST_Research')

# Set output encoding
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("="*70)
print("Testing Ab3 Regeneration (After Healer Fix)")
print("="*70)

# Configure environment
os.environ.setdefault('FLASK_ENV', 'development')

try:
    from core.code_generator import auto_generate_skill_code
    
    skill_config = {
        'skill_id': 1,
        'ablation_id': 3,
        'regenerate': True
    }
    
    print("\nTesting with config:")
    print("   Skill ID: 1")
    print("   Ablation: Ab3 (Full Healing + Mojibake Fix)")
    print("   Mode: Regenerate = True\n")
    
    result = auto_generate_skill_code(**skill_config)
    
    if result['success']:
        print("\n[SUCCESS] Generation successful!")
        file_path = result['file_path']
        print("File: " + file_path)
        
        # Verify file
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print("Size: {} bytes".format(len(content)))
            
            # Check for mojibake
            mojibake = any(c in content for c in ['冽', '嚗', '靽', '瑕', '漲', '澆'])
            print("Mojibake: {}".format("FOUND" if mojibake else "None (OK)"))
            
            # Check for undefined functions
            bad_funcs = []
            for func in ['polynomial_to_string']:
                if func + '(' in content and 'def ' + func + '(' not in content:
                    bad_funcs.append(func)
            
            if bad_funcs:
                print("Undefined functions: {}".format(", ".join(bad_funcs)))
            else:
                print("No undefined function calls (OK)")
            
            # Try compile
            try:
                compile(content, file_path, 'exec')
                print("Syntax: VALID (OK)")
            except SyntaxError as e:
                print("Syntax error: {}".format(e))
        else:
            print("ERROR: File not found!")
    else:
        error = result.get('error', 'Unknown error')
        print("\n[FAILED] Error: {}".format(error))

except Exception as e:
    import traceback
    print("\nException: {}".format(e))
    traceback.print_exc()

print("\n" + "="*70)
