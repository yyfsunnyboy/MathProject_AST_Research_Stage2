# Copilot Instructions for Smart-Edu AIGC Platform

## Project Overview
- This project is an AI-powered adaptive content generation engine for education, focused on digitizing textbooks, generating algorithmic question banks, and providing intelligent tutoring for high school mathematics.
- The codebase is organized around four core modules:
  1. **Textbook Importer**: Converts unstructured documents (PDF/Word) into structured chapter databases and example sets.
  2. **Auto-Code Sync**: Transforms static questions into executable Python scripts for dynamic question generation. Uses strict prompting and AST self-healing to ensure code quality.
  3. **Pedagogical Enricher**: Generates Socratic guidance prompts for each question, following a pedagogical trilogy (initiate-strategy-check).
  4. **Knowledge Graph Builder**: Analyzes skill dependencies to build adaptive learning paths across grade levels.

## Key Conventions & Patterns
- **Python 3.9+** is required. Main scripts are in the project root; utility and module scripts are named by function (e.g., `check_*.py`, `test_*.py`).
- **Database**: Uses SQLite in WAL mode for concurrency. Initialization via `python utils/init_db.py`.
- **AI Integration**: Prompts and code generation leverage Google Gemini Pro APIs. API keys are set in `.env`.
- **Content as Code**: All generated question scripts are Python files (see `skills/*.py` if present).
- **Testing**: Test scripts are named `test_*.py` and cover both data validation and code generation logic.
- **Error Handling**: Many scripts use retry mechanisms and self-healing AST patterns to ensure robustness of generated code.

## Developer Workflows
- **Setup**: Install dependencies with `pip install -r requirements.txt`. Copy `.env.example` to `.env` and set API keys.
- **Run**: Start the app with `python app.py`. Access at `http://127.0.0.1:5000`.
- **Database**: Initialize with `python utils/init_db.py`.
- **Debugging**: Use scripts like `debug_db_check.py`, `debug_master_spec.py`, and `debug_schema.py` for targeted troubleshooting.
- **Data/Content Checks**: Scripts prefixed with `check_` and `show_` are for validation and inspection of data, database, and generated content.
- **Regeneration**: Use `regenerate_ab1_v2.py`, `regenerate_ab2_prompt.py`, etc., to refresh question sets or prompts.

## Integration Points
- **External APIs**: Google Gemini Pro (API key required).
- **Document Processing**: Uses `clean_pandoc` for LaTeX/Markdown cleaning.
- **Visualization**: Matplotlib and MathJax for math rendering.

## Examples
- To validate new question generation: `python generate_and_validate_applications.py`
- To check database tables: `python show_db_tables.py`
- To run all ablation tests: `python test_all_ablations_format.py`

## References
- See `README.md` for full system overview and setup.
- See `docs/軟體設計文件 (SDD).md` for detailed architecture and data flow.
- For new modules, follow the naming and modularization patterns in the root directory.

---
*For AI agents: Always prefer existing script patterns and leverage the retry/self-healing logic for any code generation or data transformation tasks. When in doubt, reference the most similar `check_`, `test_`, or `debug_` script for implementation style.*
