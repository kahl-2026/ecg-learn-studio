# Contributing to ECG Learn Studio

Thank you for your interest in contributing!

## Development Setup

```bash
# Clone the repository
git clone <repo-url>
cd ecg-learn-studio

# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install Python dependencies
cd ml-python
python3 -m pip install -e ".[dev]"

# Build Rust TUI
cd ../tui-rust
cargo build
```

## Code Style

### Rust
- Follow standard Rust conventions
- Run `cargo fmt` before committing
- Run `cargo clippy` and address warnings
- Document public APIs with rustdoc comments

### Python
- Follow PEP 8 style guide
- Use type hints where applicable
- Run `black` for formatting
- Run `ruff` for linting
- Use docstrings for all public functions

## Testing

```bash
# Run Rust tests
cd tui-rust
cargo test

# Run Python tests
cd ml-python
pytest tests/

# Run all tests
make test
```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with clear commit messages
3. Add tests for new functionality
4. Update documentation as needed
5. Run linters and tests
6. Submit PR with clear description

## Reporting Issues

When reporting bugs, include:
- OS and version
- Rust/Python versions
- Steps to reproduce
- Expected vs actual behavior
- Relevant error messages

## Code of Conduct

Be respectful, inclusive, and constructive in all interactions.

## Questions?

Open a discussion or issue on the repository.
