# Development Installation

Install the package in development mode with testing dependencies:

```bash
pip install -e ".[dev]"
```

# Running Tests

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=brainwidemap --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_statistics.py
```

# Code Style

Format code with Black:
```bash
black brainwidemap/ tests/
```

Check code style with flake8:
```bash
flake8 brainwidemap/ tests/
```

# Type Checking

Run type checks with mypy:
```bash
mypy brainwidemap/
```
