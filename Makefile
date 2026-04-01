.PHONY: help build run test lint clean install download-datasets

# Default target
help:
	@echo "ECG Learn Studio - Build System"
	@echo ""
	@echo "Available targets:"
	@echo "  make install          - Install dependencies (Rust + Python)"
	@echo "  make build            - Build Rust TUI"
	@echo "  make run              - Run the application"
	@echo "  make test             - Run all tests"
	@echo "  make lint             - Run linters and formatters"
	@echo "  make clean            - Clean build artifacts"
	@echo "  make download-datasets - Download public ECG datasets"
	@echo ""

# Install dependencies
install: install-rust install-python

install-rust:
	@echo "Installing Rust dependencies..."
	cd tui-rust && cargo build --release

install-python:
	@echo "Installing Python dependencies..."
	cd ml-python && python3 -m pip install -e .

# Build
build:
	@echo "Building Rust TUI..."
	cd tui-rust && cargo build --release

# Run application
run: build
	@echo "Starting ECG Learn Studio..."
	cd tui-rust && cargo run --release

# Testing
test: test-rust test-python

test-rust:
	@echo "Running Rust tests..."
	cd tui-rust && cargo test

test-python:
	@echo "Running Python tests..."
	cd ml-python && python3 -m pytest tests/

# Linting
lint: lint-rust lint-python

lint-rust:
	@echo "Linting Rust code..."
	cd tui-rust && cargo fmt --check
	cd tui-rust && cargo clippy -- -D warnings

lint-python:
	@echo "Linting Python code..."
	cd ml-python && python3 -m black --check src/
	cd ml-python && python3 -m ruff check src/
	cd ml-python && python3 -m mypy src/

# Format code
format: format-rust format-python

format-rust:
	cd tui-rust && cargo fmt

format-python:
	cd ml-python && python3 -m black src/
	cd ml-python && python3 -m ruff check --fix src/

# Clean
clean:
	@echo "Cleaning build artifacts..."
	cd tui-rust && cargo clean
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf ml-python/build ml-python/dist ml-python/*.egg-info

# Download datasets
download-datasets:
	@echo "Downloading ECG datasets..."
	bash scripts/download-datasets.sh

# Development setup
dev-setup: install
	@echo "Setting up development environment..."
	cd ml-python && python3 -m pip install -e ".[dev]"
	@echo "Creating config template..."
	cp config.example.toml config.toml || true

# Create sample data
sample-data:
	@echo "Generating sample synthetic data..."
	cd ml-python && python3 -m ecg_learn.data.synthetic --output ../datasets/synthetic/ --count 100
