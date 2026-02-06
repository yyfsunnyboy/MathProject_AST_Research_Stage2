# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: gemini-2.5-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 36.26s | Tokens: In=260, Out=388
# Created At: 2026-02-05 23:59:38
# Fix Status: [Basic Cleanup Only] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random
import re

def _poly_to_string(poly_terms):
    """
    Converts a list of (coefficient, exponent) tuples into a formatted polynomial string.
    Example: [(3, 3), (-5, 2), (2, 0)] -> "3x^3-5x^2+2"
    """
    # Filter out zero coefficients and sort by exponent in descending order
    poly_terms = sorted([t for t in poly_terms if t[0] != 0], key=lambda x: x[1], reverse=True)

    if not poly_terms:
        return "0"

    parts = []
    for i, (coeff, exp) in enumerate(poly_terms):
        term_str = ""
        abs_coeff = abs(coeff)

        # Determine sign
        if coeff < 0:
            sign = "-"
        elif i > 0: # Positive coefficient, not the first term
            sign = "+"
        else: # Positive coefficient, first term
            sign = ""

        # Determine coefficient part
        coeff_part = ""
        if exp == 0: # Constant term
            coeff_part = str(abs_coeff)
        elif abs_coeff == 1: # Coefficient is 1 or -1, don't show '1'
            coeff_part = ""
        else:
            coeff_part = str(abs_coeff)

        # Determine exponent part
        exp_part = ""
        if exp == 1:
            exp_part = "x"
        elif exp > 1:
            exp_part = f"x^{exp}"
        # If exp == 0, exp_part remains empty

        # Combine parts
        if exp == 0: # Special case for constant term
            term_str = f"{sign}{coeff_part}"
        else:
            term_str = f"{sign}{coeff_part}{exp_part}"
        
        parts.append(term_str)
    
    return "".join(parts)

def _