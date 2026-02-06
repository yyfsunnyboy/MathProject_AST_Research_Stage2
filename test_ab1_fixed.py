#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the fixed Ab1 skill"""
import sys
sys.path.insert(0, '.')

from skills.jh_數學1上_FourArithmeticOperationsOfIntegers_14b_Ab1 import generate

print("=== Ab1 Skill Test ===")
for i in range(5):
    result = generate()
    print(f"\nTest {i+1}:")
    print(f"  Question: {result['question_text']}")
    print(f"  Answer:   {result['correct_answer']}")

print("\n✅ All tests completed successfully!")
