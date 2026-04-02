# Contributing

## Development Setup

```bash
# Clone the repository
git clone git@github.com:gautam2905/Digital-Twin.git
cd Digital-Twin

# Install runtime dependencies
pip install -r requirements.txt

# Install training dependencies (optional, for model retraining)
pip install -r requirements-training.txt

# Run the dashboard
python -m webapp.app
```

## Branch Naming Convention

- `feature/<name>` — New features
- `fix/<name>` — Bug fixes
- `docs/<name>` — Documentation changes
- `test/<name>` — Test additions

## Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new feature
fix: resolve bug
docs: update documentation
test: add tests
chore: maintenance tasks
refactor: code restructuring
```

Reference issues with `Refs #N` or `Closes #N`.

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with clear commit messages
3. Ensure all tests pass: `pytest tests/ -v`
4. Push and create a PR against `main`
5. Request review from at least one team member
6. PR must pass CI checks before merge

## Code Style

- Python: Follow PEP 8 (max line length 120)
- JavaScript: Standard style
- CSS: BEM-like naming for classes

## Running Tests

```bash
pytest tests/ -v
```

## Project Team

| Name | Focus Area |
|------|-----------|
| Gautam Gupta | ML model, backend integration, documentation |
| Yash Verma | Inference engine, dashboard UI, tests |
| Utkarsh Mishra | Data pipeline, simulator, configuration |
