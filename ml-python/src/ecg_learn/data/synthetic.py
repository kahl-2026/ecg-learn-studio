"""Synthetic ECG Generator - Generate realistic ECG signals for 5 arrhythmia classes"""

import numpy as np
from typing import Literal, Tuple
import warnings

ArrhythmiaType = Literal['normal', 'afib', 'bradycardia', 'tachycardia', 'pvc']


class SyntheticECGGenerator:
    """Generate synthetic ECG signals with controllable arrhythmia characteristics."""
    
    def __init__(self, sampling_rate: int = 360, seed: int = 42):
        """
        Initialize synthetic ECG generator.
        
        Args:
            sampling_rate: Samples per second (default 360 Hz, MIT-BIH standard)
            seed: Random seed for reproducibility
        """
        self.sampling_rate = sampling_rate
        self.rng = np.random.RandomState(seed)
        
    def generate(
        self,
        arrhythmia_type: ArrhythmiaType,
        duration: float = 10.0,
        noise_level: float = 0.05,
        heart_rate: float = None
    ) -> Tuple[np.ndarray, dict]:
        """
        Generate a synthetic ECG signal.
        
        Args:
            arrhythmia_type: Type of arrhythmia to simulate
            duration: Signal duration in seconds
            noise_level: Noise amplitude (0.0 to 0.2 typical)
            heart_rate: Override default heart rate for the arrhythmia type
            
        Returns:
            signal: ECG signal array
            metadata: Dictionary with generation parameters
        """
        n_samples = int(duration * self.sampling_rate)
        
        # Set default heart rates for each arrhythmia type
        hr_defaults = {
            'normal': 75.0,
            'afib': 110.0,
            'bradycardia': 45.0,
            'tachycardia': 130.0,
            'pvc': 72.0
        }
        
        hr = heart_rate if heart_rate is not None else hr_defaults[arrhythmia_type]
        
        # Generate base signal
        if arrhythmia_type == 'normal':
            signal = self._generate_normal(n_samples, hr)
        elif arrhythmia_type == 'afib':
            signal = self._generate_afib(n_samples, hr)
        elif arrhythmia_type == 'bradycardia':
            signal = self._generate_bradycardia(n_samples, hr)
        elif arrhythmia_type == 'tachycardia':
            signal = self._generate_tachycardia(n_samples, hr)
        elif arrhythmia_type == 'pvc':
            signal = self._generate_pvc(n_samples, hr)
        else:
            raise ValueError(f"Unknown arrhythmia type: {arrhythmia_type}")
        
        # Add noise
        if noise_level > 0:
            noise = self.rng.normal(0, noise_level, n_samples)
            signal += noise
        
        metadata = {
            'arrhythmia_type': arrhythmia_type,
            'duration': duration,
            'sampling_rate': self.sampling_rate,
            'heart_rate': hr,
            'noise_level': noise_level
        }
        
        return signal, metadata
    
    def _generate_normal(self, n_samples: int, hr: float) -> np.ndarray:
        """Generate normal sinus rhythm."""
        signal = np.zeros(n_samples)
        t = np.arange(n_samples) / self.sampling_rate
        
        # Calculate beat interval
        beat_interval = 60.0 / hr
        n_beats = int(n_samples / (beat_interval * self.sampling_rate))
        
        for i in range(n_beats):
            beat_pos = int(i * beat_interval * self.sampling_rate)
            signal += self._create_pqrst_complex(t, beat_pos / self.sampling_rate)
        
        return signal
    
    def _generate_afib(self, n_samples: int, hr: float) -> np.ndarray:
        """Generate atrial fibrillation - irregular RR intervals, no clear P waves."""
        signal = np.zeros(n_samples)
        t = np.arange(n_samples) / self.sampling_rate
        
        # Irregular beat intervals
        avg_interval = 60.0 / hr
        current_time = 0.0
        
        while current_time < (n_samples / self.sampling_rate):
            # Irregular intervals (±30% variation)
            interval = avg_interval * self.rng.uniform(0.7, 1.3)
            beat_pos = int(current_time * self.sampling_rate)
            
            if beat_pos < n_samples:
                # No P wave in AFib, just QRS-T
                signal += self._create_qrst_complex(t, current_time)
                # Add fibrillation waves
                signal += self._add_fib_waves(t, current_time, interval)
            
            current_time += interval
        
        return signal
    
    def _generate_bradycardia(self, n_samples: int, hr: float) -> np.ndarray:
        """Generate bradycardia - slow heart rate (<60 bpm)."""
        # Similar to normal but slower
        return self._generate_normal(n_samples, hr)
    
    def _generate_tachycardia(self, n_samples: int, hr: float) -> np.ndarray:
        """Generate tachycardia - fast heart rate (>100 bpm)."""
        # Similar to normal but faster
        return self._generate_normal(n_samples, hr)
    
    def _generate_pvc(self, n_samples: int, hr: float) -> np.ndarray:
        """Generate signal with premature ventricular contractions."""
        signal = np.zeros(n_samples)
        t = np.arange(n_samples) / self.sampling_rate
        
        beat_interval = 60.0 / hr
        n_beats = int(n_samples / (beat_interval * self.sampling_rate))
        
        for i in range(n_beats):
            beat_pos = int(i * beat_interval * self.sampling_rate)
            
            # Every 4-6 beats, insert a PVC
            if i % self.rng.randint(4, 7) == 0:
                signal += self._create_pvc_complex(t, beat_pos / self.sampling_rate)
            else:
                signal += self._create_pqrst_complex(t, beat_pos / self.sampling_rate)
        
        return signal
    
    def _create_pqrst_complex(self, t: np.ndarray, center: float) -> np.ndarray:
        """Create a normal PQRST complex centered at given time."""
        signal = np.zeros_like(t)
        
        # P wave (atrial depolarization)
        p_amp, p_width = 0.15, 0.08
        signal += p_amp * np.exp(-((t - (center - 0.16)) ** 2) / (2 * p_width ** 2))
        
        # Q wave
        q_amp, q_width = -0.05, 0.02
        signal += q_amp * np.exp(-((t - (center - 0.04)) ** 2) / (2 * q_width ** 2))
        
        # R wave (main QRS peak)
        r_amp, r_width = 1.2, 0.03
        signal += r_amp * np.exp(-((t - center) ** 2) / (2 * r_width ** 2))
        
        # S wave
        s_amp, s_width = -0.2, 0.03
        signal += s_amp * np.exp(-((t - (center + 0.04)) ** 2) / (2 * s_width ** 2))
        
        # T wave (ventricular repolarization)
        t_amp, t_width = 0.3, 0.12
        signal += t_amp * np.exp(-((t - (center + 0.25)) ** 2) / (2 * t_width ** 2))
        
        return signal
    
    def _create_qrst_complex(self, t: np.ndarray, center: float) -> np.ndarray:
        """Create QRS-T complex without P wave (for AFib)."""
        signal = np.zeros_like(t)
        
        # QRS complex
        r_amp, r_width = 1.1, 0.03
        signal += r_amp * np.exp(-((t - center) ** 2) / (2 * r_width ** 2))
        
        s_amp, s_width = -0.15, 0.03
        signal += s_amp * np.exp(-((t - (center + 0.04)) ** 2) / (2 * s_width ** 2))
        
        # T wave
        t_amp, t_width = 0.25, 0.10
        signal += t_amp * np.exp(-((t - (center + 0.22)) ** 2) / (2 * t_width ** 2))
        
        return signal
    
    def _create_pvc_complex(self, t: np.ndarray, center: float) -> np.ndarray:
        """Create a premature ventricular contraction - wide, bizarre QRS."""
        signal = np.zeros_like(t)
        
        # Wide QRS (>0.12s)
        r_amp, r_width = 1.4, 0.06  # Wider than normal
        signal += r_amp * np.exp(-((t - center) ** 2) / (2 * r_width ** 2))
        
        # Deep S wave
        s_amp, s_width = -0.4, 0.05
        signal += s_amp * np.exp(-((t - (center + 0.08)) ** 2) / (2 * s_width ** 2))
        
        # Inverted or abnormal T wave
        t_amp, t_width = -0.2, 0.15
        signal += t_amp * np.exp(-((t - (center + 0.30)) ** 2) / (2 * t_width ** 2))
        
        return signal
    
    def _add_fib_waves(self, t: np.ndarray, center: float, duration: float) -> np.ndarray:
        """Add atrial fibrillation waves (small irregular oscillations)."""
        signal = np.zeros_like(t)
        
        # Small amplitude, high frequency oscillations
        for i in range(5):
            freq = self.rng.uniform(4, 8)
            amp = self.rng.uniform(0.02, 0.05)
            phase = self.rng.uniform(0, 2 * np.pi)
            
            mask = (t >= center) & (t < center + duration)
            signal[mask] += amp * np.sin(2 * np.pi * freq * (t[mask] - center) + phase)
        
        return signal
    
    def generate_dataset(
        self,
        n_samples_per_class: int = 100,
        duration: float = 10.0,
        noise_level: float = 0.05
    ) -> Tuple[np.ndarray, np.ndarray, list]:
        """
        Generate a balanced dataset of all arrhythmia types.
        
        Args:
            n_samples_per_class: Number of examples per arrhythmia class
            duration: Duration of each signal in seconds
            noise_level: Noise level
            
        Returns:
            signals: Array of shape (n_total, n_timepoints)
            labels: Array of integer labels (0-4)
            label_names: List of label names
        """
        classes: list[ArrhythmiaType] = ['normal', 'afib', 'bradycardia', 'tachycardia', 'pvc']
        n_timepoints = int(duration * self.sampling_rate)
        n_total = n_samples_per_class * len(classes)
        
        signals = np.zeros((n_total, n_timepoints))
        labels = np.zeros(n_total, dtype=int)
        
        idx = 0
        for class_idx, arrhythmia in enumerate(classes):
            for _ in range(n_samples_per_class):
                signal, _ = self.generate(arrhythmia, duration, noise_level)
                signals[idx] = signal
                labels[idx] = class_idx
                idx += 1
        
        return signals, labels, classes


if __name__ == '__main__':
    # Demo generation
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate synthetic ECG data')
    parser.add_argument('--output', default='../datasets/synthetic/', help='Output directory')
    parser.add_argument('--count', type=int, default=100, help='Samples per class')
    args = parser.parse_args()
    
    generator = SyntheticECGGenerator()
    signals, labels, label_names = generator.generate_dataset(n_samples_per_class=args.count)
    
    import os
    os.makedirs(args.output, exist_ok=True)
    np.save(os.path.join(args.output, 'signals.npy'), signals)
    np.save(os.path.join(args.output, 'labels.npy'), labels)
    
    with open(os.path.join(args.output, 'labels.txt'), 'w') as f:
        for name in label_names:
            f.write(f"{name}\n")
    
    print(f"Generated {len(signals)} synthetic ECG signals in {args.output}")
    print(f"Shape: {signals.shape}, Labels: {label_names}")
