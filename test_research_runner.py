#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test research_runner with fixed Ab3 skill"""

import subprocess
import sys

# Simulate user input: select skill 5, sample 3
test_input = "5\n3\n"

print("Testing research_runner with gh_ApplicationsOfDerivatives_14B_Ab3...")
print("=" * 70)

try:
    result = subprocess.run(
        [sys.executable, "scripts/research_runner.py"],
        input=test_input,
        text=True,
        capture_output=True,
        timeout=60,
        cwd="."
    )
    
    # Print last 100 lines of output
    output_lines = result.stdout.split('\n')
    for line in output_lines[-100:]:
        print(line)
    
    if result.returncode == 0:
        print("\n" + "=" * 70)
        print("✅ Research runner completed successfully!")
    else:
        print("\n" + "=" * 70)
        print(f"❌ Failed with return code {result.returncode}")
        if result.stderr:
            print("STDERR:", result.stderr[-500:])
        
except subprocess.TimeoutExpired:
    print("❌ Timeout! Script took more than 60 seconds")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
