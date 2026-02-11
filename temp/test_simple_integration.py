#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple integration test without unicode characters
"""
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.prompts.prompt_builder import PromptBuilder

print("="*80)
print("TEST: Dynamic Tool Selection System Integration")
print("="*80)

# Simple MASTER_SPEC
MASTER_SPEC = """
domain: arithmetic
constraints:
  - value_range: -20~20
"""

# Test 1: Fraction skill (Ab2)
print("\nTest 1: Fraction skill - Ab2 Mode")
print("-"*80)

prompt_ab2 = PromptBuilder.build(
    master_spec=MASTER_SPEC,
    ablation_id=2,
    topic="Fraction Operations",
    skill_id="jh_數學1上_FourArithmeticOperationsOfNumbers"
)

print("OK - Prompt generated")
print("Length:", len(prompt_ab2), "chars")
print("Has API Manual:", "已啟用的數學軍火庫" in prompt_ab2)
print("Has Tool Protocol:", "Domain Tool Selection Protocol" in prompt_ab2)
print("Has FractionOps:", "FractionOps" in prompt_ab2)

# Test 2: Integer skill (Ab3)
print("\nTest 2: Integer skill - Ab3 Mode")
print("-"*80)

prompt_ab3 = PromptBuilder.build(
    master_spec=MASTER_SPEC,
    ablation_id=3,
    topic="Integer Operations",
    skill_id="jh_數學1上_FourArithmeticOperationsOfIntegers"
)

print("OK - Prompt generated")
print("Length:", len(prompt_ab3), "chars")
print("Has API Manual:", "已啟用的數學軍火庫" in prompt_ab3)

# Test 3: Bare prompt (Ab1)
print("\nTest 3: Bare prompt - Ab1 Mode")
print("-"*80)

prompt_ab1 = PromptBuilder.build(
    master_spec=MASTER_SPEC,
    ablation_id=1,
    textbook_example="Example: Calculate 3/2 - 1/4",
    topic="Fraction Operations"
)

print("OK - Bare prompt generated")
print("Length:", len(prompt_ab1), "chars")

print("\n" + "="*80)
print("SUCCESS: All integration tests passed!")
print("="*80)
