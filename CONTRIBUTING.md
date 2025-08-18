## Contributing

- Use Python 3.11 and the provided venv.
- Install tooling: `pip install -e .[dev]` and `pre-commit install`.
- Run checks locally before pushing: `ruff`, `black --check`, `mypy`, `pytest -q`.
- Keep edits small and focused; include tests when adding behavior.
- Do not commit secrets or real credentials.

### Pull Requests

- Target `main` or appropriate feature branch.
- Ensure CI is green and coverage ≥ 80%.
- Include a clear description and test plan.

### Code Owners

We use CODEOWNERS to route reviews for Phase 3 changes. See `.github/CODEOWNERS`.
