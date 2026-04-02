"""Test data loading and synthetic generation."""

import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ecg_learn.data import SyntheticECGGenerator, ECGDataLoader


class TestSyntheticECGGenerator:
    """Test synthetic ECG data generation."""
    
    @pytest.fixture
    def generator(self):
        """Create a synthetic ECG generator."""
        return SyntheticECGGenerator(sampling_rate=360, signal_length=3600, seed=42)
    
    def test_generate_normal_beat(self, generator):
        """Test generating a normal sinus rhythm beat."""
        signal = generator.generate_normal_sinus()
        
        assert isinstance(signal, np.ndarray)
        assert len(signal) == generator.signal_length
        assert not np.any(np.isnan(signal))
        assert not np.any(np.isinf(signal))
    
    def test_generate_bradycardia(self, generator):
        """Test generating bradycardia."""
        signal = generator.generate_bradycardia()
        
        assert isinstance(signal, np.ndarray)
        assert len(signal) == generator.signal_length
    
    def test_generate_tachycardia(self, generator):
        """Test generating tachycardia."""
        signal = generator.generate_tachycardia()
        
        assert isinstance(signal, np.ndarray)
        assert len(signal) == generator.signal_length
    
    def test_generate_afib(self, generator):
        """Test generating atrial fibrillation."""
        signal = generator.generate_atrial_fibrillation()
        
        assert isinstance(signal, np.ndarray)
        assert len(signal) == generator.signal_length
    
    def test_generate_pvc(self, generator):
        """Test generating PVC."""
        signal = generator.generate_pvc()
        
        assert isinstance(signal, np.ndarray)
        assert len(signal) == generator.signal_length
    
    def test_generate_dataset(self, generator):
        """Test generating a full dataset."""
        n_per_class = 20
        signals, labels, label_names = generator.generate_dataset(n_samples_per_class=n_per_class)
        
        assert signals.shape[0] == n_per_class * len(label_names)
        assert len(labels) == signals.shape[0]
        assert len(label_names) == 5  # 5 classes
        
        # Check balanced classes
        unique, counts = np.unique(labels, return_counts=True)
        assert all(count == n_per_class for count in counts)
    
    def test_reproducibility(self, generator):
        """Test that seed produces reproducible results."""
        gen1 = SyntheticECGGenerator(seed=42)
        gen2 = SyntheticECGGenerator(seed=42)
        
        signal1 = gen1.generate_normal_sinus()
        signal2 = gen2.generate_normal_sinus()
        
        np.testing.assert_array_almost_equal(signal1, signal2)
    
    def test_different_seeds_different_results(self):
        """Test that different seeds produce different results."""
        gen1 = SyntheticECGGenerator(seed=42)
        gen2 = SyntheticECGGenerator(seed=123)
        
        signal1 = gen1.generate_normal_sinus()
        signal2 = gen2.generate_normal_sinus()
        
        assert not np.allclose(signal1, signal2)


class TestECGDataLoader:
    """Test the ECG data loader."""
    
    @pytest.fixture
    def loader(self):
        """Create a data loader with test path."""
        return ECGDataLoader(base_dir='../datasets')
    
    def test_validate_dataset_valid(self, loader):
        """Test dataset validation with valid data."""
        signals = np.random.randn(100, 360)
        labels = np.random.randint(0, 5, 100)
        
        result = loader.validate_dataset(signals, labels)
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
        assert 'stats' in result
        assert result['stats']['n_samples'] == 100
    
    def test_validate_dataset_shape_mismatch(self, loader):
        """Test validation catches shape mismatch."""
        signals = np.random.randn(100, 360)
        labels = np.random.randint(0, 5, 50)  # Wrong size
        
        result = loader.validate_dataset(signals, labels)
        
        assert result['valid'] is False
        assert len(result['errors']) > 0
    
    def test_validate_dataset_wrong_dimensions(self, loader):
        """Test validation catches wrong dimensions."""
        signals = np.random.randn(100)  # 1D instead of 2D
        labels = np.random.randint(0, 5, 100)
        
        result = loader.validate_dataset(signals, labels)
        
        assert result['valid'] is False
    
    def test_validate_dataset_nan_warning(self, loader):
        """Test validation warns about NaN values."""
        signals = np.random.randn(100, 360)
        signals[0, 0] = np.nan
        labels = np.random.randint(0, 5, 100)
        
        result = loader.validate_dataset(signals, labels)
        
        assert any('NaN' in w for w in result['warnings'])
    
    def test_get_dataset_info(self, loader):
        """Test getting dataset info."""
        info = loader.get_dataset_info('synthetic')
        
        assert 'name' in info
        assert 'available' in info
    
    def test_load_dataset_method(self, loader):
        """Test the unified load_dataset method."""
        # This will fail if dataset doesn't exist, which is expected
        try:
            signals, labels, names = loader.load_dataset('synthetic')
            assert signals.shape[0] == len(labels)
        except FileNotFoundError:
            # Expected if synthetic data hasn't been generated
            pass


class TestDataQuality:
    """Test data quality characteristics."""
    
    def test_signal_range(self):
        """Test that synthetic signals have reasonable amplitude."""
        gen = SyntheticECGGenerator(seed=42)
        signals, _, _ = gen.generate_dataset(n_samples_per_class=10)
        
        # Signals should be roughly normalized
        assert signals.min() > -10
        assert signals.max() < 10
    
    def test_signal_variability(self):
        """Test that signals are not constant."""
        gen = SyntheticECGGenerator(seed=42)
        signals, _, _ = gen.generate_dataset(n_samples_per_class=10)
        
        # Each signal should have some variance
        for signal in signals:
            assert np.std(signal) > 0.01


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
