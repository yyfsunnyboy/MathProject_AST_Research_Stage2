#!/usr/bin/env python3
"""Debug Ab3 generation failure"""
import sys
import traceback
from skills.gh_ApplicationsOfDerivatives_14b_Ab3 import generate

print("=" * 60)
print("Testing Ab3 Generation")
print("=" * 60)

try:
    result = generate(level=1)
    print("✅ Generation succeeded")
    print(f"\nResult keys: {result.keys()}")
    if 'q' in result:
        print(f"Question preview: {result['q'][:200]}...")
    if 'a' in result:
        print(f"Answer preview: {result['a'][:200]}...")
except Exception as e:
    print(f"❌ Generation failed with error:")
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    print("\nFull traceback:")
    traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("HEALER DIAGNOSIS NEEDED")
    print("=" * 60)
