#!/bin/bash
# Download ECG datasets from PhysioNet

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATASETS_DIR="$PROJECT_ROOT/datasets"

echo "ECG Learn Studio - Dataset Downloader"
echo "======================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required"
    exit 1
fi

# Create datasets directory
mkdir -p "$DATASETS_DIR"

echo "This script will download public ECG datasets from PhysioNet"
echo "Total download size: ~500MB"
echo ""
echo "Datasets:"
echo "  - MIT-BIH Arrhythmia Database (~50MB)"
echo "  - PTB-XL ECG Database (~450MB)"
echo ""

read -p "Continue with download? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Download cancelled"
    exit 0
fi

# Download using Python script
cd "$PROJECT_ROOT/ml-python"
python3 -m ecg_learn.data.downloader --output "$DATASETS_DIR" --dataset all

echo ""
echo "✓ Datasets downloaded successfully!"
echo "  Location: $DATASETS_DIR"
