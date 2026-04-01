"""ECG Feature Extraction - Extract clinical and statistical features"""

import numpy as np
from typing import Dict, List
from scipy import stats, signal


class ECGFeatureExtractor:
    """Extract features from ECG signals for ML models."""
    
    def __init__(self, sampling_rate: int = 360):
        """
        Initialize feature extractor.
        
        Args:
            sampling_rate: Signal sampling rate in Hz
        """
        self.sampling_rate = sampling_rate
    
    def extract_time_domain(self, ecg_signal: np.ndarray, r_peaks: np.ndarray = None) -> Dict:
        """
        Extract time-domain features.
        
        Args:
            ecg_signal: ECG signal
            r_peaks: Optional R-peak locations
            
        Returns:
            Dictionary of time-domain features
        """
        features = {}
        
        # Basic statistics
        features['mean'] = float(np.mean(ecg_signal))
        features['std'] = float(np.std(ecg_signal))
        features['min'] = float(np.min(ecg_signal))
        features['max'] = float(np.max(ecg_signal))
        features['range'] = features['max'] - features['min']
        features['skewness'] = float(stats.skew(ecg_signal))
        features['kurtosis'] = float(stats.kurtosis(ecg_signal))
        
        # Signal energy
        features['energy'] = float(np.sum(ecg_signal ** 2))
        
        # Zero crossing rate
        zero_crossings = np.sum(np.diff(np.sign(ecg_signal)) != 0)
        features['zero_crossing_rate'] = zero_crossings / len(ecg_signal)
        
        if r_peaks is not None and len(r_peaks) > 1:
            # RR interval features
            rr_intervals = np.diff(r_peaks) / self.sampling_rate
            
            features['mean_rr'] = float(np.mean(rr_intervals))
            features['std_rr'] = float(np.std(rr_intervals))
            features['rmssd'] = float(np.sqrt(np.mean(np.diff(rr_intervals) ** 2)))
            
            # Heart rate
            features['mean_hr'] = 60.0 / features['mean_rr'] if features['mean_rr'] > 0 else 0
            features['std_hr'] = features['std_rr'] * (60.0 / features['mean_rr'] ** 2)
        
        return features
    
    def extract_frequency_domain(self, ecg_signal: np.ndarray) -> Dict:
        """
        Extract frequency-domain features using FFT.
        
        Args:
            ecg_signal: ECG signal
            
        Returns:
            Dictionary of frequency-domain features
        """
        features = {}
        
        # Compute FFT
        fft = np.fft.fft(ecg_signal)
        freqs = np.fft.fftfreq(len(ecg_signal), 1/self.sampling_rate)
        
        # Use only positive frequencies
        positive_freqs = freqs[:len(freqs)//2]
        magnitudes = np.abs(fft[:len(fft)//2])
        
        # Power spectral density
        psd = magnitudes ** 2
        
        # Dominant frequency
        dominant_idx = np.argmax(psd)
        features['dominant_frequency'] = float(positive_freqs[dominant_idx])
        features['dominant_power'] = float(psd[dominant_idx])
        
        # Frequency bands (for HRV analysis)
        vlf = (0.003, 0.04)  # Very low frequency
        lf = (0.04, 0.15)     # Low frequency
        hf = (0.15, 0.4)      # High frequency
        
        for band_name, (low, high) in [('vlf', vlf), ('lf', lf), ('hf', hf)]:
            mask = (positive_freqs >= low) & (positive_freqs <= high)
            features[f'{band_name}_power'] = float(np.sum(psd[mask]))
        
        # LF/HF ratio (sympatho-vagal balance)
        if features['hf_power'] > 0:
            features['lf_hf_ratio'] = features['lf_power'] / features['hf_power']
        else:
            features['lf_hf_ratio'] = 0.0
        
        # Spectral entropy
        normalized_psd = psd / (np.sum(psd) + 1e-10)
        features['spectral_entropy'] = float(-np.sum(normalized_psd * np.log2(normalized_psd + 1e-10)))
        
        return features
    
    def extract_morphological(self, ecg_signal: np.ndarray, r_peaks: np.ndarray) -> Dict:
        """
        Extract morphological features (QRS width, amplitudes, etc.).
        
        Args:
            ecg_signal: ECG signal
            r_peaks: R-peak locations
            
        Returns:
            Dictionary of morphological features
        """
        features = {}
        
        if len(r_peaks) == 0:
            return features
        
        # QRS complex features
        qrs_durations = []
        r_amplitudes = []
        
        for r_peak in r_peaks:
            # QRS duration (approximate as width at 50% height)
            if 0 < r_peak < len(ecg_signal) - 1:
                r_amp = ecg_signal[r_peak]
                r_amplitudes.append(r_amp)
                
                # Find QRS onset and offset
                search_window = int(0.1 * self.sampling_rate)  # 100ms window
                start = max(0, r_peak - search_window)
                end = min(len(ecg_signal), r_peak + search_window)
                
                # Simple width estimation
                threshold = r_amp * 0.5
                qrs_segment = ecg_signal[start:end]
                above_threshold = qrs_segment > threshold
                
                if np.any(above_threshold):
                    qrs_width_samples = np.sum(above_threshold)
                    qrs_width_seconds = qrs_width_samples / self.sampling_rate
                    qrs_durations.append(qrs_width_seconds)
        
        if qrs_durations:
            features['mean_qrs_duration'] = float(np.mean(qrs_durations))
            features['std_qrs_duration'] = float(np.std(qrs_durations))
        
        if r_amplitudes:
            features['mean_r_amplitude'] = float(np.mean(r_amplitudes))
            features['std_r_amplitude'] = float(np.std(r_amplitudes))
        
        return features
    
    def extract_all(
        self,
        ecg_signal: np.ndarray,
        r_peaks: np.ndarray = None,
        include_frequency: bool = True
    ) -> Dict:
        """
        Extract all features.
        
        Args:
            ecg_signal: ECG signal
            r_peaks: Optional R-peak locations
            include_frequency: Include frequency-domain features (slower)
            
        Returns:
            Dictionary of all features
        """
        features = {}
        
        # Time domain
        features.update(self.extract_time_domain(ecg_signal, r_peaks))
        
        # Frequency domain
        if include_frequency:
            features.update(self.extract_frequency_domain(ecg_signal))
        
        # Morphological (requires R-peaks)
        if r_peaks is not None:
            features.update(self.extract_morphological(ecg_signal, r_peaks))
        
        return features
    
    def extract_dataset(
        self,
        signals: np.ndarray,
        r_peaks_list: List[np.ndarray] = None
    ) -> np.ndarray:
        """
        Extract features from entire dataset.
        
        Args:
            signals: Array of signals (n_samples, signal_length)
            r_peaks_list: Optional list of R-peak arrays for each signal
            
        Returns:
            Feature matrix (n_samples, n_features)
        """
        all_features = []
        
        for i, signal_data in enumerate(signals):
            r_peaks = r_peaks_list[i] if r_peaks_list is not None else None
            features = self.extract_all(signal_data, r_peaks, include_frequency=True)
            all_features.append(features)
        
        # Convert to consistent feature matrix
        feature_names = sorted(all_features[0].keys())
        feature_matrix = np.array([
            [sample[name] for name in feature_names]
            for sample in all_features
        ])
        
        return feature_matrix
