# Conditional23 Diagnostics Evidence Scope & README

This directory contains the tools and outputs for the diagnostics stage of the 23 conditional cells of Candidate B r003.

## Evidence Scope and Nature

The 23 output files located in the `runs/{cell_id}/diagnostic_evidence.json` directories represent:
**`static AST-only diagnostics formal evidence`**

* **Analysis Method**: The candidate program source codes were statically read and parsed using Python's `ast.parse` library to extract abstract syntax structure (e.g., verifying top-level assert statement locations).
* **Zero Candidate Execution**: The import, compilation, or execution of the candidate programs was exactly **zero**.
* **Limits of Diagnostics**: This suite does NOT represent validated execution traces or dynamic outputs; it is strictly a static syntax-level proof verification of the assertion masking failures.
