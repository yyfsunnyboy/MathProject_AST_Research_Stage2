# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: gemini-2.5-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 36.20s | Tokens: In=260, Out=267
# Created At: 2026-02-06 00:00:15
# Fix Status: [Basic Cleanup Only] | Fixes: Basic=0, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random
import re

def _format_polynomial(terms):
    """
    Formats a list of (coefficient, exponent) tuples into a polynomial string.
    e.g., [(3, 3), (-5, 2), (2, 0)] -> "3x^3 - 5x^2 + 2"
    """
    # Filter out zero coefficient terms first
    non_zero_terms = [(c, e) for c, e in terms if c != 0]
    
    if not non_zero_terms:
        return "0"

    # Sort terms by exponent in descending order for canonical representation
    non_zero_terms.sort(key=lambda x: x[1], reverse=True)

    poly_str_parts = []
    for i, (coeff, exp) in enumerate(non_zero_terms):
        term_part = ""
        
        # Handle sign
        if i == 0: # First term
            if coeff < 0:
                term_part += "-"
        else: # Subsequent terms
            if coeff > 0:
                term_part += " + "
            else:
                term_part += " - "
        
        abs_coeff = abs(coeff)

        # Handle coefficient and x part
        if exp == 0: # Constant term
            term_part += str(abs_coeff)
        elif exp == 1: # x term (e.g