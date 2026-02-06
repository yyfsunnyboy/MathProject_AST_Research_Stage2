# ==============================================================================
# ID: gh_ApplicationsOfDerivatives
# Model: gemini-2.5-flash | Strategy: V10.1 Modular Refactored
# Ablation ID: 1 | Basic Cleanup: ENABLED | Advanced Healer: OFF
# Performance: 38.49s | Tokens: In=260, Out=1138
# Created At: 2026-02-06 00:00:54
# Fix Status: [Basic Cleanup Only] | Fixes: Basic=1, Advanced=None
# Verification: Internal Logic Check = PASSED
# ==============================================================================

import random
import re

def _format_polynomial_string(terms):
    """
    Helper function to format a polynomial from a list of (coefficient, exponent) tuples
    into a standard string representation.
    e.g., [(3, 3), (-5, 2), (2, 0)] -> "3x^3 - 5x^2 + 2"
    """
    if not terms:
        return "0"

    # Normalize terms: combine like terms and sort by exponent in descending order
    term_dict = {}
    for coeff, exp in terms:
        if coeff != 0:
            term_dict[exp] = term_dict.get(exp, 0) + coeff

    sorted_terms = sorted([(coeff, exp) for exp, coeff in term_dict.items() if coeff != 0], key=lambda x: x[1], reverse=True)

    if not sorted_terms:
        return "0"

    poly_str_parts = []
    for i, (coeff, exp) in enumerate(sorted_terms):
        term_str = ""
        
        # Determine sign
        if coeff > 0 and i > 0:
            term_str += "+"
        elif coeff < 0:
            term_str += "-"
        
        abs_coeff = abs(coeff)

        # Coefficient and exponent part
        if exp == 0: # Constant term
            term_str += str(abs_coeff)
        elif abs_coeff == 1: # x^n or x
            if exp == 1:
                term_str += "x"
            else:
                term_str += "x^" + str(exp)
        else: # General case ax^n or ax
            term_str += str(abs_coeff)
            if exp == 1:
                term_str += "x"
            elif exp > 1:
                term_str += "x^" + str(exp)

        poly_str_parts.append(term_str)

    return "".join(poly_str_parts)

def _parse_polynomial_string(poly_str):
    """
    Helper function to parse a polynomial string into a list of (coefficient, exponent) tuples.
    e.g., "3x^3 - 5x^2 + 2" -> [(3, 3), (-5, 2), (2, 0)]