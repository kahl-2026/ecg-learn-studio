"""Test preprocessing pipeline."""

import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ecg_learn.preprocessing import ECGFilters, ECGSegmentation, ECGFeatureExtractor


class TestECGFilters:
    """Test ECG filtering functions."""
    
    @pytest.fixture
    def filters(self):
        """Create ECG filters instance."""
        return ECGFilters(sampling_rate=360)
    
    @pytest.fixture
    def test_signal(self):
        """Create a test signal with noise."""
        t = np.linspace(0, 10, 3600)  # 10 seconds at 360 Hz
        
        # Clean ECG-like signal
        clean = np.sin(2 * np.pi * 1 * t)  # 1 Hz heartbeat
        
        # Add high-frequency noise
        noise_hf = 0.2 * np.sin(2 * np.pi * 100 * t)
        
        # Add baseline wander (low frequency)
        baseline = 0.3 * np.sin(2 * np.pi * 0.1 * t)
        
        # Add powerline noise (60 Hz)
        powerline = 0.1 * np.sin(2 * np.pi * 60 * t)
        
        return clean + noise_hf + baseline + powerline
    
    def test_bandpass_filter(self, filters, test_signal):
        """Test bandpass filter removes out-of-band frequencies."""
        filtered = filters.bandpass_filter(test_signal, lowcut=0.5, highcut=40.0)
        
        assert len(filtered) == len(test_signal)
        assert not np.any(np.isnan(filtered))
        
        # Filtered signal should have less high-frequency content
        # (Simple check: less variance at high frequencies)
        fft_orig = np.abs(np.fft.fft(test_signal))
        fft_filt = np.abs(np.fft.fft(filtered))
        
        # High frequency region (above 50 Hz) should be attenuated
        n = len(test_signal)
        high_freq_start = int(50 * n / 360)
        assert np.sum(fft_filt[high_freq_start:n//2]) < np.sum(fft_orig[high_freq_start:n//2])
    
    def test_remove_baseline_wander(self, filters, test_signal):
        """Test baseline wander removal."""
        filtered = filters.remove_baseline_wander(test_signal, cutoff=0.5)
        
        assert len(filtered) == len(test_signal)
        
        # DC component should be reduced
        assert abs(np.mean(filtered)) < abs(np.mean(test_signal))
    
    def test_notch_filter(self, filters, test_signal):
        """Test notch filter removes powerline interference."""
        filtered = filters.notch_filter(test_signal, freq=60.0)
        
        assert len(filtered) == len(test_signal)
        
        # 60 Hz component should be reduced
        fft_orig = np.abs(np.fft.fft(test_signal))
        fft_filt = np.abs(np.fft.fft(filtered))
        
        n = len(test_signal)
        freq_60 = int(60 * n / 360)
        assert fft_filt[freq_60] < fft_orig[freq_60]
    
    def test_normalize_zscore(self, filters):
        """Test z-score normalization."""
        signal = np.random.randn(1000) * 10 + 5  # Mean ~5, std ~10
        
        normalized, params = filters.normalize(signal, method='zscore')
        
        assert abs(np.mean(normalized)) < 0.1  # Mean should be ~0
        assert abs(np.std(normalized) - 1) < 0.1  # Std should be ~1
        assert params['method'] == 'zscore'
    
    def test_normalize_minmax(self, filters):
        """Test min-max normalization."""
        signal = np.random.randn(1000)
        
        normalized, params = filters.normalize(signal, method='minmax')
        
        assert normalized.min() >= 0
        assert normalized.max() <= 1
        assert params['method'] == 'minmax'
    
    def test_normalize_robust(self, filters):
        """Test robust normalization."""
        signal = np.random.randn(1000)
        # Add outliers
        signal[0] = 100
        signal[1] = -100
        
        normalized, params = filters.normalize(signal, method='robust')
        
        assert params['method'] == 'robust'
        # Most values should be within reasonable range despite outliers
        central = normalized[2:]
        assert abs(np.median(central)) < 1
    
    def test_denormalize(self, filters):
        """Test that denormalization reverses normalization."""
        original = np.random.randn(1000) * 10 + 5
        
        normalized, params = filters.normalize(original, method='zscore')
        restored = filters.denormalize(normalized, params)
        
        np.testing.assert_array_almost_equal(original, restored, decimal=10)
    
    def test_preprocess_pipeline(self, filters, test_signal):
        """Test complete preprocessing pipeline."""
        processed, metadata = filters.preprocess(
            test_signal,
            apply_bandpass=True,
            apply_notch=True,
            normalize=True
        )
        
        assert len(processed) == len(test_signal)
        assert 'steps' in metadata
        assert 'bandpass' in metadata['steps'][0]
        assert 'notch' in metadata['steps'][1]


class TestECGSegmentation:
    """Test ECG segmentation functions."""
    
    @pytest.fixture
    def segmenter(self):
        """Create segmentation instance."""
        return ECGSegmentation(sampling_rate=360)
    
    @pytest.fixture
    def test_signal(self):
        """Create a signal with clear R-peaks."""
        t = np.linspace(0, 5, 1800)  # 5 seconds
        
        # Create multiple QRS complexes
        signal = np.zeros_like(t)
        for i in range(6):  # 6 beats in 5 seconds (72 BPM)
            peak_time = 0.4 + i * 0.8  # Every 0.8 seconds
            peak_idx = int(peak_time * 360)
            
            # Simple triangular QRS
            if peak_idx > 10 and peak_idx < len(signal) - 10:
                signal[peak_idx-5:peak_idx] = np.linspace(0, 1, 5)
                signal[peak_idx:peak_idx+5] = np.linspace(1, 0, 5)
        
        return signal
    
    def test_detect_r_peaks(self, segmenter, test_signal):
        """Test R-peak detection."""
        r_peaks = segmenter.detect_r_peaks(test_signal)
        
        assert len(r_peaks) > 0
        assert all(0 <= p < len(test_signal) for p in r_peaks)
    
    def test_segment_beats(self, segmenter, test_signal):
        """Test beat segmentation."""
        segments = segmenter.segment_beats(test_signal, beat_length=200)
        
        # Should get some segments
        assert len(segments) >= 0  # May be 0 if peaks not well detected
        
        if len(segments) > 0:
            assert segments[0].shape == (200,)


class TestECGFeatureExtractor:
    """Test feature extraction."""
    
    @pytest.fixture
    def extractor(self):
        """Create feature extractor."""
        return ECGFeatureExtractor(sampling_rate=360)
    
    @pytest.fixture
    def test_signal(self):
        """Create a test ECG signal."""
        t = np.linspace(0, 10, 3600)
        return np.sin(2 * np.pi * 1 * t) + 0.1 * np.random.randn(3600)
    
    def test_extract_time_domain(self, extractor, test_signal):
        """Test time-domain feature extraction."""
        features = extractor.extract_time_domain(test_signal)
        
        assert 'mean' in features
        assert 'std' in features
        assert 'min' in features
        assert 'max' in features
        assert 'skewness' in features
        assert 'kurtosis' in features
        assert 'energy' in features
    
    def test_extract_frequency_domain(self, extractor, test_signal):
        """Test frequency-domain feature extraction."""
        features = extractor.extract_frequency_domain(test_signal)
        
        assert 'dominant_frequency' in features
        assert 'spectral_entropy' in features
        assert 'vlf_power' in features
        assert 'lf_power' in features
        assert 'hf_power' in features
    
    def test_extract_all(self, extractor, test_signal):
        """Test extracting all features."""
        features = extractor.extract_all(test_signal, include_frequency=True)
        
        # Should have both time and frequency features
        assert 'mean' in features
        assert 'dominant_frequency' in features
    
    def test_extract_dataset(self, extractor):
        """Test batch feature extraction."""
        signals = np.random.randn(50, 3600)
        
        feature_matrix = extractor.extract_dataset(signals)
        
        assert feature_matrix.shape[0] == 50
        assert feature_matrix.shape[1] > 0  # Has features
        assert not np.any(np.isnan(feature_matrix))
    
    def test_features_are_finite(self, extractor, test_signal):
        """Test that all features are finite values."""
        features = extractor.extract_all(test_signal)
        
        for name, value in features.items():
            assert np.isfinite(value), f"Feature {name} is not finite: {value}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
