"""ECG Segmentation - Beat detection, R-peak finding, windowing"""

import numpy as np
from scipy import signal
from typing import List, Tuple


class ECGSegmentation:
    """ECG signal segmentation and beat detection."""
    
    def __init__(self, sampling_rate: int = 360):
        """
        Initialize segmentation.
        
        Args:
            sampling_rate: Signal sampling rate in Hz
        """
        self.sampling_rate = sampling_rate
    
    def detect_r_peaks(
        self,
        ecg_signal: np.ndarray,
        min_distance: float = 0.3
    ) -> np.ndarray:
        """
        Detect R-peaks using Pan-Tompkins algorithm (simplified).
        
        Args:
            ecg_signal: Preprocessed ECG signal
            min_distance: Minimum distance between peaks in seconds
            
        Returns:
            Array of R-peak indices
        """
        # Differentiate to emphasize QRS slope
        diff = np.diff(ecg_signal)
        
        # Square to make all values positive and emphasize larger slopes
        squared = diff ** 2
        
        # Moving average to smooth
        window_size = int(0.15 * self.sampling_rate)  # 150ms window
        kernel = np.ones(window_size) / window_size
        smoothed = np.convolve(squared, kernel, mode='same')
        
        # Find peaks with minimum distance
        min_samples = int(min_distance * self.sampling_rate)
        peaks, _ = signal.find_peaks(
            smoothed,
            distance=min_samples,
            prominence=np.std(smoothed) * 0.5
        )
        
        return peaks
    
    def segment_beats(
        self,
        ecg_signal: np.ndarray,
        r_peaks: np.ndarray | None = None,
        beat_length: int | None = None,
        before: float = 0.2,
        after: float = 0.4
    ) -> List[np.ndarray]:
        """
        Segment individual beats around R-peaks.
        
        Args:
            ecg_signal: ECG signal
            r_peaks: Optional R-peak indices (auto-detected when omitted)
            beat_length: Optional fixed beat window length in samples (compatibility mode)
            before: Time before R-peak to include (seconds)
            after: Time after R-peak to include (seconds)
            
        Returns:
            List of beat segments
        """
        if r_peaks is None:
            r_peaks = self.detect_r_peaks(ecg_signal)

        if beat_length is not None:
            before_samples = beat_length // 2
            after_samples = beat_length - before_samples
        else:
            before_samples = int(before * self.sampling_rate)
            after_samples = int(after * self.sampling_rate)
        
        beats = []
        for r_peak in r_peaks:
            start = max(0, r_peak - before_samples)
            end = min(len(ecg_signal), r_peak + after_samples)
            
            # Only include if full window available
            if (r_peak - start) == before_samples and (end - r_peak) == after_samples:
                beat = ecg_signal[start:end]
                beats.append(beat)
        
        return beats
    
    def create_fixed_windows(
        self,
        ecg_signal: np.ndarray,
        window_duration: float = 10.0,
        overlap: float = 0.0
    ) -> List[Tuple[np.ndarray, int]]:
        """
        Create fixed-duration windows from signal.
        
        Args:
            ecg_signal: ECG signal
            window_duration: Window duration in seconds
            overlap: Overlap fraction (0.0 to 0.99)
            
        Returns:
            List of (window, start_index) tuples
        """
        window_samples = int(window_duration * self.sampling_rate)
        step_samples = int(window_samples * (1 - overlap))
        
        windows = []
        start = 0
        
        while start + window_samples <= len(ecg_signal):
            window = ecg_signal[start:start + window_samples]
            windows.append((window, start))
            start += step_samples
        
        return windows
    
    def compute_rr_intervals(
        self,
        r_peaks: np.ndarray
    ) -> Tuple[np.ndarray, dict]:
        """
        Compute RR intervals from R-peaks.
        
        Args:
            r_peaks: R-peak indices
            
        Returns:
            RR intervals in seconds and statistics
        """
        if len(r_peaks) < 2:
            return np.array([]), {}
        
        # Compute intervals in samples, convert to seconds
        rr_samples = np.diff(r_peaks)
        rr_seconds = rr_samples / self.sampling_rate
        
        # Compute statistics
        stats = {
            'mean_rr': float(np.mean(rr_seconds)),
            'std_rr': float(np.std(rr_seconds)),
            'min_rr': float(np.min(rr_seconds)),
            'max_rr': float(np.max(rr_seconds)),
            'heart_rate': 60.0 / np.mean(rr_seconds) if np.mean(rr_seconds) > 0 else 0
        }
        
        return rr_seconds, stats
    
    def detect_abnormal_beats(
        self,
        rr_intervals: np.ndarray,
        threshold: float = 1.5
    ) -> np.ndarray:
        """
        Detect abnormal beats based on RR interval variation.
        
        Args:
            rr_intervals: RR intervals in seconds
            threshold: Number of standard deviations for outlier detection
            
        Returns:
            Boolean array indicating abnormal beats
        """
        if len(rr_intervals) < 3:
            return np.zeros(len(rr_intervals), dtype=bool)
        
        mean_rr = np.mean(rr_intervals)
        std_rr = np.std(rr_intervals)
        
        # Intervals outside threshold*std are considered abnormal
        abnormal = np.abs(rr_intervals - mean_rr) > (threshold * std_rr)
        
        return abnormal
    
    def segment_dataset(
        self,
        signals: np.ndarray,
        method: str = 'fixed',
        **kwargs
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Segment entire dataset.
        
        Args:
            signals: Array of shape (n_samples, signal_length)
            method: 'fixed' or 'beat'
            **kwargs: Arguments for segmentation method
            
        Returns:
            Segmented signals and corresponding original indices
        """
        all_segments = []
        all_indices = []
        
        for i, signal_data in enumerate(signals):
            if method == 'fixed':
                window_duration = kwargs.get('window_duration', 10.0)
                overlap = kwargs.get('overlap', 0.0)
                windows = self.create_fixed_windows(signal_data, window_duration, overlap)
                
                for window, _ in windows:
                    all_segments.append(window)
                    all_indices.append(i)
            
            elif method == 'beat':
                r_peaks = self.detect_r_peaks(signal_data)
                before = kwargs.get('before', 0.2)
                after = kwargs.get('after', 0.4)
                beat_length = kwargs.get('beat_length')
                beats = self.segment_beats(
                    signal_data,
                    r_peaks=r_peaks,
                    beat_length=beat_length,
                    before=before,
                    after=after,
                )
                
                for beat in beats:
                    all_segments.append(beat)
                    all_indices.append(i)
            
            else:
                raise ValueError(f"Unknown segmentation method: {method}")
        
        return np.array(all_segments), np.array(all_indices)
