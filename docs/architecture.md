# ECG Learn Studio - Architecture Guide

## Overview

ECG Learn Studio is a terminal-based educational platform for learning ECG interpretation and experimenting with machine learning models. The architecture is designed to be modular, performant, and educational-first.

## Design Principles

1. **Educational Focus**: All features prioritize learning and understanding over clinical accuracy
2. **Offline-First**: No cloud dependencies, runs entirely on local machine
3. **Fast & Responsive**: Rust TUI ensures sub-100ms response times
4. **Beginner-Friendly**: Plain language, progressive complexity, extensive help

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                     │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │   Rust TUI (ratatui + crossterm)                    │    │
│  │                                                       │    │
│  │  • Event Loop (keyboard, rendering)                 │    │
│  │  • Screen Management (Home, Learn, Train, etc.)     │    │
│  │  • Chart Rendering (ASCII/Unicode ECG waveforms)    │    │
│  │  • Theme System (Default, Colorblind, Monochrome)   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ JSON over stdin/stdout
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Communication Layer                        │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │   JSON RPC Protocol (v1.0)                          │    │
│  │                                                       │    │
│  │  • Request/Response pattern                         │    │
│  │  • Progress updates for long operations             │    │
│  │  • Error handling with codes                        │    │
│  │  • Version compatibility checking                   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend Services Layer                    │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │   Python ML Backend                                  │    │
│  │                                                       │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │  API Server (stdin/stdout JSON RPC)          │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  │                                                       │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │  Data Management                              │   │    │
│  │  │  • Synthetic ECG Generator                   │   │    │
│  │  │  • Dataset Loader (MIT-BIH, PTB-XL)          │   │    │
│  │  │  • Data Validation                           │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  │                                                       │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │  Preprocessing Pipeline                       │   │    │
│  │  │  • Filters (bandpass, notch)                 │   │    │
│  │  │  • Normalization                             │   │    │
│  │  │  • Segmentation (beat detection)             │   │    │
│  │  │  • Feature Extraction                        │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  │                                                       │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │  ML Models                                    │   │    │
│  │  │  • Baseline (LogReg, Random Forest)          │   │    │
│  │  │  • Neural (1D CNN)                           │   │    │
│  │  │  • Model Registry                            │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  │                                                       │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │  Training & Evaluation                        │   │    │
│  │  │  • Unified Trainer                           │   │    │
│  │  │  • Metrics (Acc, Prec, Rec, F1, AUC)        │   │    │
│  │  │  • Checkpoint Management                     │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  │                                                       │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │  Inference & Explainability                   │   │    │
│  │  │  • Predictor (with confidence)               │   │    │
│  │  │  • Explainer (feature importance, saliency)  │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  │                                                       │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │  Educational Content                          │   │    │
│  │  │  • Lesson Manager (10+ lessons)              │   │    │
│  │  │  • Glossary (50+ terms)                      │   │    │
│  │  │  • Quiz Bank (50+ questions)                 │   │    │
│  │  │  • Progress Tracking                         │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Technology Choices

### Why Rust for TUI?

**Pros:**
- **Performance**: Sub-millisecond rendering, instant key response
- **Safety**: No crashes from memory bugs, safe concurrency
- **Binary**: Single executable, no runtime dependencies
- **Ecosystem**: ratatui is mature, well-maintained, feature-rich

**Cons:**
- Longer compile times (mitigated by incremental compilation)
- Steeper learning curve for contributors

**Verdict**: Rust provides the best terminal UX. Performance and reliability are worth the tradeoff.

### Why Python for ML Backend?

**Pros:**
- **Ecosystem**: NumPy, SciPy, PyTorch, scikit-learn are unmatched
- **Rapid Development**: Quick iteration on ML pipelines
- **Community**: Extensive ECG signal processing libraries (wfdb, neurokit2)
- **Education**: Most ML learners know Python

**Cons:**
- Slower than compiled languages (acceptable for educational use)
- Dependency management can be complex

**Verdict**: Python is the clear choice for ML/signal processing. The ecosystem advantage is overwhelming.

### Why JSON over stdin/stdout?

**Alternatives Considered:**
1. **gRPC**: Too heavy, adds complexity
2. **HTTP REST**: Requires port management, potential conflicts
3. **Shared Memory**: Platform-specific, complex
4. **Unix Sockets**: Similar to stdin/stdout but more setup

**Verdict**: JSON over stdio is:
- Simple to debug (can pipe/redirect)
- No port conflicts
- No networking overhead
- Language-agnostic
- Easy to test

## Data Flow

### Training a Model

```
User presses "T" in TUI
    ↓
Rust: Send JSON request to Python
    {"method": "train_model", "params": {"model_type": "cnn", ...}}
    ↓
Python: Receive request
    ↓
Python: Load dataset, preprocess
    ↓
Python: Train model with progress updates
    (sends progress JSON to stderr)
    ↓
Rust: Display live training metrics
    ↓
Python: Evaluate model, send final response
    {"success": true, "result": {"metrics": {...}}}
    ↓
Rust: Display final results
```

### Making a Prediction

```
User selects ECG signal
    ↓
Rust: Send predict request
    {"method": "predict", "params": {"model_id": "...", "data": [...]}}
    ↓
Python: Run inference
    ↓
Python: Compute confidence, explanations
    ↓
Python: Send response
    {"prediction": "AFib", "confidence": 0.92, ...}
    ↓
Rust: Display prediction with explanation
```

## ML Pipeline

### Signal Preprocessing

1. **Bandpass Filter (0.5-40 Hz)**
   - Remove baseline wander (<0.5 Hz)
   - Remove high-frequency noise (>40 Hz)
   - Preserve QRS complex (5-15 Hz)

2. **Normalization**
   - Z-score normalization (mean=0, std=1)
   - Robust to outliers

3. **Segmentation**
   - **Beat-based**: Extract individual heartbeats
   - **Fixed-window**: 10-second segments for rhythm classification

4. **Feature Extraction** (baseline models only)
   - Time-domain: mean, std, skewness, kurtosis
   - Frequency-domain: dominant frequency, spectral entropy
   - Morphological: QRS width, R-peak amplitude
   - HRV: RR intervals, RMSSD

### Model Selection

| Model | Input | Use Case | Training Time | Accuracy |
|-------|-------|----------|--------------|----------|
| Logistic Regression | Features | Baseline, interpretable | Seconds | ~75% |
| Random Forest | Features | Robust, feature importance | Seconds | ~80% |
| 1D CNN | Raw signal | Best performance | Minutes | ~85% |

### Class Imbalance Handling

- **Class Weights**: Weight inversely proportional to frequency
- **Stratified Splitting**: Preserve class distribution in train/val/test
- **Evaluation**: Use macro-averaged metrics (not just accuracy)

## Security & Safety

### Safety Disclaimers

Displayed in:
- Home screen (always visible)
- README (prominent warning)
- Prediction results (with every output)
- Documentation

### Data Privacy

- **No telemetry**: Zero data collection
- **Local only**: All processing on-device
- **No cloud**: No API calls, no internet dependency
- **No PHI**: No patient-identifiable data supported

### Input Validation

- All user inputs validated before processing
- JSON schema enforcement
- Signal length/format checks
- Model input dimension verification

## Performance Targets

| Operation | Target | Achieved |
|-----------|--------|----------|
| Key press to render | <100ms | ~50ms |
| Screen switch | <50ms | ~20ms |
| Backend ping | <100ms | ~50ms |
| Synthetic data gen (100 samples) | <1s | ~0.5s |
| Baseline model training | <30s | ~10s |
| CNN training (50 epochs) | <5min | ~3min |
| Inference | <100ms | ~50ms |

## Future Enhancements

### Potential Additions (Not in Scope)

1. **Real-time ECG streaming**: Live data from hardware
2. **12-lead ECG support**: Currently single-lead only
3. **Advanced CNN architectures**: ResNet, Attention mechanisms
4. **Transfer learning**: Pre-trained models
5. **Web interface**: Browser-based alternative to TUI
6. **Multi-language support**: i18n for lessons

### Extensibility

The architecture supports:
- Adding new models via `ModelRegistry`
- Adding lessons via JSON/TOML configuration
- Custom preprocessing pipelines
- Plugin system for external datasets

## Development Workflow

```bash
# Backend development
cd ml-python
python3 -m pytest tests/          # Run tests
python3 -m mypy src/               # Type checking
python3 -m black src/              # Format
python3 -m ruff check src/         # Lint

# Frontend development
cd tui-rust
cargo build                        # Build
cargo test                         # Test
cargo clippy                       # Lint
cargo fmt                          # Format

# Integration testing
make test                          # Run all tests
make run                           # End-to-end test
```

## Troubleshooting

### Common Issues

**Issue**: Backend fails to start
- **Check**: Python 3.11+ installed
- **Check**: Dependencies installed (`pip install -e .`)
- **Fix**: Run from project root

**Issue**: Rust compilation errors
- **Check**: Rust 1.70+ installed
- **Fix**: `rustup update`

**Issue**: Protocol version mismatch
- **Check**: Rust and Python code in sync
- **Fix**: Rebuild both components

## Performance Profiling

### Rust TUI

```bash
cargo build --release
cargo flamegraph --bin ecg-learn-tui
```

### Python Backend

```python
import cProfile
cProfile.run('train_model(...)', 'output.prof')
```

## License

MIT License - See LICENSE file.

## Contributors

See CONTRIBUTING.md for development guidelines.
