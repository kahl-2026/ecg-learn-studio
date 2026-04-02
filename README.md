# ECG Learn Studio

> ⚠️ **EDUCATIONAL USE ONLY** - Not for medical diagnosis or emergency use. This is a learning and research platform.

A beginner-friendly, terminal-based ECG learning and machine learning analysis platform designed for education and research.

## Features

### 🎓 Interactive Learning
- **ECG Basics**: Step-by-step lessons on P waves, QRS complex, T waves, and intervals
- **Progressive Difficulty**: Beginner and intermediate explanation modes
- **Built-in Glossary**: 50+ ECG terms with clear definitions
- **Quiz Mode**: Test your knowledge with 50+ questions across multiple categories

### 📊 Signal Analysis
- **Signal Explorer**: Visualize ECG waveforms with ASCII/Unicode charts
- **Real & Synthetic Data**: Support for MIT-BIH, PTB-XL datasets plus synthetic generator
- **Preprocessing Pipeline**: Filtering, normalization, beat detection
- **Feature Extraction**: RR intervals, QRS duration, heart rate variability

### 🤖 Machine Learning
- **Multiple Models**: Logistic Regression, Random Forest, 1D CNN
- **5-Class Classification**: Normal, AFib, Bradycardia, Tachycardia, PVC
- **Training Visualization**: Real-time metrics, confusion matrices
- **Explainable AI**: Feature importance and prediction explanations
- **Educational Focus**: Plain-English metric explanations

### 🖥️ Terminal UI
- **Fast & Responsive**: Built with Rust and ratatui
- **Keyboard-Driven**: Efficient navigation with hotkeys
- **Accessible**: Colorblind-safe and monochrome themes
- **Cross-Platform**: Works on Linux, macOS, Windows

## Architecture

```
┌─────────────────────────────────────────┐
│         Rust TUI Frontend               │
│  (ratatui + crossterm)                  │
│                                         │
│  Screens: Home, Learn, Explorer,        │
│          Train, Predict, Quiz           │
└───────────────┬─────────────────────────┘
                │ JSON over stdin/stdout
┌───────────────▼─────────────────────────┐
│      Python ML Backend                  │
│  (NumPy, SciPy, PyTorch, scikit-learn)  │
│                                         │
│  Services: Data, Preprocessing, ML,     │
│           Training, Inference, Education│
└─────────────────────────────────────────┘
```

### Why This Architecture?
- **Rust TUI**: Fast, responsive, safe concurrency, excellent terminal UX
- **Python Backend**: Best ecosystem for ECG signal processing and ML
- **JSON IPC**: Simple, debuggable, language-agnostic communication

## Quick Start

### Prerequisites
- Rust 1.70+ ([install](https://rustup.rs/))
- Python 3.11+ with pip
- Linux/macOS/Windows with a modern terminal

### Installation

```bash
# Clone or extract the project
cd ecg-learn-studio

# Install dependencies
make install
# or run full bootstrap
./scripts/setup.sh

# Build the application
make build

# Generate sample data
make sample-data

# Run ECG Learn Studio
make run
```

`./scripts/setup.sh` now checks requirement compatibility first and only installs missing/incompatible packages, avoiding repeated reinstalls.

### First Steps

1. **Press `L`** to start learning ECG basics
2. **Press `E`** to explore sample ECG signals
3. **Press `T`** to train your first model
4. **Press `Z`** to test your knowledge with Quiz mode
5. **Press `?`** for help anytime

## Downloading Real Datasets

```bash
# Download MIT-BIH and PTB-XL datasets (requires internet)
make download-datasets

# This will download ~500MB of data
# Datasets are stored in datasets/ directory
```

## Project Structure

```
ecg-learn-studio/
├── tui-rust/          # Rust TUI application
│   ├── src/
│   │   ├── main.rs
│   │   ├── app.rs
│   │   ├── ui/        # Screen implementations
│   │   └── backend/   # Python backend manager
│   └── Cargo.toml
├── ml-python/         # Python ML backend
│   ├── src/ecg_learn/
│   │   ├── api/       # JSON API server
│   │   ├── data/      # Data loading & generation
│   │   ├── preprocessing/
│   │   ├── models/    # ML models
│   │   ├── training/
│   │   ├── inference/
│   │   ├── education/ # Lessons & glossary
│   │   └── quiz/
│   └── pyproject.toml
├── shared-schema/     # IPC protocol definition
├── datasets/          # ECG data
├── docs/              # Documentation
└── Makefile
```

## Documentation

- [Architecture Guide](docs/architecture.md) - Design decisions and component overview
- [ML Guide](docs/ml-guide.md) - Models, datasets, metrics explained
- [IPC Protocol](shared-schema/README.md) - Communication specification
- [Contributing](docs/contributing.md) - Development guidelines

## Safety & Ethics

This platform is designed for **education and research only**:

- ❌ Not approved for medical diagnosis
- ❌ Not for clinical decision-making
- ❌ Not for emergency situations
- ✅ For learning ECG interpretation
- ✅ For ML research and experimentation
- ✅ For educational demonstrations

**Always consult qualified medical professionals for health concerns.**

## Dataset Attribution

- **MIT-BIH Arrhythmia Database**: Moody GB, Mark RG. The impact of the MIT-BIH Arrhythmia Database. IEEE Eng in Med and Biol 20(3):45-50 (May-June 2001).
- **PTB-XL Database**: Wagner, P., et al. PTB-XL, a large publicly available electrocardiography dataset. Scientific Data 7.1 (2020): 1-15.

Both datasets are available from PhysioNet under open-access licenses.

## Development

```bash
# Run tests
make test

# Run linters
make lint

# Format code
make format

# Clean build artifacts
make clean
```

## System Requirements

- **Memory**: 2GB RAM minimum, 4GB recommended
- **Storage**: 1GB free space (5GB with datasets)
- **Terminal**: 80x24 minimum, 120x40 recommended
- **CPU**: Any modern CPU (ML training is CPU-optimized)

## License

MIT License - See LICENSE file for details.

## Acknowledgments

- Built with [ratatui](https://github.com/ratatui-org/ratatui) - Terminal UI library
- ML powered by [PyTorch](https://pytorch.org/) and [scikit-learn](https://scikit-learn.org/)
- Signal processing with [SciPy](https://scipy.org/) and [WFDB](https://github.com/MIT-LCP/wfdb-python)
- Datasets from [PhysioNet](https://physionet.org/)

## Version

**v1.0.0** - Initial Release

---

**Questions or Issues?** Check the docs/ directory or open an issue on the project repository.
