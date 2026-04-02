"""Pytest configuration and shared fixtures."""

import pytest
import numpy as np
import sys
from pathlib import Path

# Ensure src is in path
src_path = Path(__file__).parent.parent / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
def random_seed():
    """Fixed random seed for reproducibility."""
    return 42


@pytest.fixture(scope="session")
def sample_ecg_signal():
    """Generate a sample ECG signal for testing."""
    np.random.seed(42)
    t = np.linspace(0, 10, 3600)  # 10 seconds at 360 Hz
    
    # Create a simple ECG-like signal
    signal = np.zeros_like(t)
    
    # Add QRS complexes every ~1 second (60 BPM)
    for i in range(10):
        peak_time = 0.5 + i * 1.0
        peak_idx = int(peak_time * 360)
        
        if peak_idx < len(signal) - 50:
            # P wave
            p_start = peak_idx - 40
            if p_start > 0:
                p_wave = 0.1 * np.exp(-((np.arange(20) - 10)**2) / 20)
                signal[p_start:p_start+20] += p_wave
            
            # QRS complex
            signal[peak_idx-5:peak_idx] = np.linspace(0, 1, 5)
            signal[peak_idx:peak_idx+5] = np.linspace(1, -0.2, 5)
            signal[peak_idx+5:peak_idx+10] = np.linspace(-0.2, 0, 5)
            
            # T wave
            t_start = peak_idx + 20
            if t_start + 30 < len(signal):
                t_wave = 0.15 * np.exp(-((np.arange(30) - 15)**2) / 50)
                signal[t_start:t_start+30] += t_wave
    
    # Add small noise
    signal += 0.02 * np.random.randn(len(signal))
    
    return signal


@pytest.fixture(scope="session")
def synthetic_dataset():
    """Generate a small synthetic dataset for testing."""
    from ecg_learn.data import SyntheticECGGenerator
    
    gen = SyntheticECGGenerator(seed=42)
    signals, labels, label_names = gen.generate_dataset(n_samples_per_class=20)
    
    return {
        'signals': signals,
        'labels': labels,
        'label_names': label_names
    }


@pytest.fixture(scope="session")
def feature_matrix(synthetic_dataset):
    """Extract features from synthetic dataset."""
    from ecg_learn.preprocessing import ECGFeatureExtractor
    
    extractor = ECGFeatureExtractor()
    features = extractor.extract_dataset(synthetic_dataset['signals'])
    
    return features


# Configure pytest
def pytest_configure(config):
    """Configure pytest settings."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
