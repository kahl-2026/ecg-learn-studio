"""ECG Signal Filters - Bandpass filtering, baseline removal, normalization"""

import numpy as np
from scipy import signal
from typing import Tuple


class ECGFilters:
    """Collection of filters for ECG signal preprocessing."""
    
    def __init__(self, sampling_rate: int = 360):
        """
        Initialize ECG filters.
        
        Args:
            sampling_rate: Signal sampling rate in Hz
        """
        self.sampling_rate = sampling_rate
    
    def bandpass_filter(
        self,
        ecg_signal: np.ndarray,
        lowcut: float = 0.5,
        highcut: float = 40.0,
        order: int = 4
    ) -> np.ndarray:
        """
        Apply bandpass filter to remove noise and baseline wander.
        
        Args:
            ecg_signal: Input ECG signal
            lowcut: Low cutoff frequency (Hz) - removes baseline wander
            highcut: High cutoff frequency (Hz) - removes high-frequency noise
            order: Filter order
            
        Returns:
            Filtered signal
        """
        nyquist = 0.5 * self.sampling_rate
        low = lowcut / nyquist
        high = highcut / nyquist
        
        b, a = signal.butter(order, [low, high], btype='band')
        filtered = signal.filtfilt(b, a, ecg_signal)
        
        return filtered
    
    def remove_baseline_wander(
        self,
        ecg_signal: np.ndarray,
        cutoff: float = 0.5
    ) -> np.ndarray:
        """
        Remove baseline wander using high-pass filter.
        
        Args:
            ecg_signal: Input ECG signal
            cutoff: Cutoff frequency (Hz)
            
        Returns:
            Signal with baseline removed
        """
        nyquist = 0.5 * self.sampling_rate
        normalized_cutoff = cutoff / nyquist
        
        b, a = signal.butter(4, normalized_cutoff, btype='high')
        filtered = signal.filtfilt(b, a, ecg_signal)
        # Remove residual DC offset introduced by filtering edges.
        filtered = filtered - np.mean(filtered)
        
        return filtered
    
    def notch_filter(
        self,
        ecg_signal: np.ndarray,
        freq: float = 60.0,
        quality: float = 30.0
    ) -> np.ndarray:
        """
        Apply notch filter to remove powerline interference.
        
        Args:
            ecg_signal: Input ECG signal
            freq: Frequency to remove (50 or 60 Hz powerline)
            quality: Quality factor
            
        Returns:
            Filtered signal
        """
        nyquist = 0.5 * self.sampling_rate
        w0 = freq / nyquist
        
        b, a = signal.iirnotch(w0, quality)
        filtered = signal.filtfilt(b, a, ecg_signal)
        
        return filtered
    
    def normalize(
        self,
        ecg_signal: np.ndarray,
        method: str = 'zscore'
    ) -> Tuple[np.ndarray, dict]:
        """
        Normalize ECG signal.
        
        Args:
            ecg_signal: Input signal
            method: 'zscore', 'minmax', or 'robust'
            
        Returns:
            Normalized signal and normalization parameters
        """
        if method == 'zscore':
            mean = np.mean(ecg_signal)
            std = np.std(ecg_signal)
            normalized = (ecg_signal - mean) / std if std > 0 else np.zeros_like(ecg_signal)
            params = {'method': 'zscore', 'mean': float(mean), 'std': float(std)}
        
        elif method == 'minmax':
            min_val = np.min(ecg_signal)
            max_val = np.max(ecg_signal)
            span = max_val - min_val
            normalized = (ecg_signal - min_val) / span if span > 0 else np.zeros_like(ecg_signal)
            params = {'method': 'minmax', 'min': float(min_val), 'max': float(max_val)}
        
        elif method == 'robust':
            # Use median and IQR for robustness to outliers
            median = np.median(ecg_signal)
            q25, q75 = np.percentile(ecg_signal, [25, 75])
            iqr = q75 - q25
            normalized = (ecg_signal - median) / iqr if iqr > 0 else np.zeros_like(ecg_signal)
            params = {'method': 'robust', 'median': float(median), 'iqr': float(iqr)}
        
        else:
            raise ValueError(f"Unknown normalization method: {method}")
        
        return normalized, params
    
    def denormalize(
        self,
        normalized_signal: np.ndarray,
        params: dict
    ) -> np.ndarray:
        """
        Reverse normalization.
        
        Args:
            normalized_signal: Normalized signal
            params: Normalization parameters from normalize()
            
        Returns:
            Original-scale signal
        """
        method = params['method']
        
        if method == 'zscore':
            return normalized_signal * params['std'] + params['mean']
        elif method == 'minmax':
            return normalized_signal * (params['max'] - params['min']) + params['min']
        elif method == 'robust':
            return normalized_signal * params['iqr'] + params['median']
        else:
            raise ValueError(f"Unknown normalization method: {method}")
    
    def preprocess(
        self,
        ecg_signal: np.ndarray,
        apply_bandpass: bool = True,
        apply_notch: bool = True,
        normalize: bool = True
    ) -> Tuple[np.ndarray, dict]:
        """
        Complete preprocessing pipeline.
        
        Args:
            ecg_signal: Raw ECG signal
            apply_bandpass: Apply bandpass filter
            apply_notch: Apply notch filter for powerline
            normalize: Normalize signal
            
        Returns:
            Preprocessed signal and metadata
        """
        processed = ecg_signal.copy()
        metadata = {'steps': []}
        
        if apply_bandpass:
            processed = self.bandpass_filter(processed)
            metadata['steps'].append('bandpass_0.5-40Hz')
        
        if apply_notch:
            processed = self.notch_filter(processed, freq=60.0)
            metadata['steps'].append('notch_60Hz')
        
        if normalize:
            processed, norm_params = self.normalize(processed, method='zscore')
            metadata['steps'].append('normalize_zscore')
            metadata['normalization'] = norm_params
        
        return processed, metadata
