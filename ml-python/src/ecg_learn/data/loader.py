"""ECG Data Loader - Load and manage ECG datasets"""

import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json


class ECGDataLoader:
    """Load ECG data from various sources (synthetic, MIT-BIH, PTB-XL)."""
    
    def __init__(self, base_dir: str = '../datasets'):
        """
        Initialize data loader.
        
        Args:
            base_dir: Base directory containing datasets
        """
        self.base_dir = Path(base_dir)
        self.loaded_datasets: Dict[str, dict] = {}
    
    def load_synthetic(self) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Load synthetic ECG dataset.
        
        Returns:
            signals: Array of shape (n_samples, n_timepoints)
            labels: Integer labels (0-4)
            label_names: List of class names
        """
        synthetic_dir = self.base_dir / 'synthetic'
        
        if not synthetic_dir.exists():
            raise FileNotFoundError(
                f"Synthetic dataset not found in {synthetic_dir}. "
                "Run: make sample-data"
            )
        
        signals = np.load(synthetic_dir / 'signals.npy')
        labels = np.load(synthetic_dir / 'labels.npy')
        
        with open(synthetic_dir / 'labels.txt', 'r') as f:
            label_names = [line.strip() for line in f]
        
        print(f"Loaded synthetic dataset: {signals.shape[0]} samples, {len(label_names)} classes")
        
        return signals, labels, label_names
    
    def load_mitbih(self, records: Optional[List[str]] = None) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Load MIT-BIH Arrhythmia Database.
        
        Args:
            records: Specific record numbers to load (e.g., ['100', '101'])
            
        Returns:
            signals: ECG signals
            labels: Beat annotations
            label_names: Annotation types
        """
        mitbih_dir = self.base_dir / 'mitbih'
        
        if not mitbih_dir.exists():
            raise FileNotFoundError(
                f"MIT-BIH dataset not found in {mitbih_dir}. "
                "Run: make download-datasets"
            )
        
        try:
            import wfdb
        except ImportError:
            raise ImportError("wfdb package required. Install with: pip install wfdb")
        
        # For now, return a placeholder indicating the dataset structure
        # Full implementation would use wfdb.rdrecord() and wfdb.rdann()
        
        print("MIT-BIH dataset loading (placeholder - implement with wfdb)")
        
        # Return dummy data structure
        return np.array([]), np.array([]), []
    
    def load_ptbxl(self, sampling_rate: int = 100) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Load PTB-XL Database.
        
        Args:
            sampling_rate: 100 or 500 Hz
            
        Returns:
            signals: ECG signals (12-lead)
            labels: Diagnostic labels
            label_names: Diagnosis names
        """
        ptbxl_dir = self.base_dir / 'ptbxl'
        
        if not ptbxl_dir.exists():
            raise FileNotFoundError(
                f"PTB-XL dataset not found in {ptbxl_dir}. "
                "Run: make download-datasets"
            )
        
        # Placeholder for PTB-XL loading
        # Full implementation would parse the CSV metadata and load signals
        
        print("PTB-XL dataset loading (placeholder)")
        
        return np.array([]), np.array([]), []
    
    def get_dataset_info(self, dataset_type: str) -> Dict:
        """
        Get information about a dataset.
        
        Args:
            dataset_type: 'synthetic', 'mitbih', or 'ptbxl'
            
        Returns:
            Dictionary with dataset metadata
        """
        if dataset_type == 'synthetic':
            try:
                signals, labels, label_names = self.load_synthetic()
                return {
                    'name': 'Synthetic ECG Dataset',
                    'n_samples': len(signals),
                    'n_classes': len(label_names),
                    'classes': label_names,
                    'sampling_rate': 360,
                    'signal_length': signals.shape[1],
                    'available': True
                }
            except FileNotFoundError:
                return {'name': 'Synthetic ECG Dataset', 'available': False}
        
        elif dataset_type == 'mitbih':
            mitbih_dir = self.base_dir / 'mitbih'
            return {
                'name': 'MIT-BIH Arrhythmia Database',
                'n_samples': 48,  # 48 records
                'sampling_rate': 360,
                'available': mitbih_dir.exists()
            }
        
        elif dataset_type == 'ptbxl':
            ptbxl_dir = self.base_dir / 'ptbxl'
            return {
                'name': 'PTB-XL Database',
                'n_samples': 21837,
                'sampling_rate': 100,  # or 500
                'available': ptbxl_dir.exists()
            }
        
        else:
            raise ValueError(f"Unknown dataset type: {dataset_type}")
    
    def validate_dataset(self, signals: np.ndarray, labels: np.ndarray) -> Dict:
        """
        Validate dataset and compute statistics.
        
        Args:
            signals: ECG signals array
            labels: Labels array
            
        Returns:
            Dictionary with validation results and statistics
        """
        validation = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': {}
        }
        
        # Check shapes
        if signals.ndim != 2:
            validation['valid'] = False
            validation['errors'].append(f"Signals should be 2D, got shape {signals.shape}")
        
        if len(signals) != len(labels):
            validation['valid'] = False
            validation['errors'].append(
                f"Signals ({len(signals)}) and labels ({len(labels)}) length mismatch"
            )
        
        # Check for NaN/Inf
        if np.any(np.isnan(signals)):
            validation['warnings'].append("Dataset contains NaN values")
        if np.any(np.isinf(signals)):
            validation['warnings'].append("Dataset contains Inf values")
        
        # Compute statistics
        validation['stats'] = {
            'n_samples': len(signals),
            'signal_length': signals.shape[1] if signals.ndim == 2 else 0,
            'n_classes': len(np.unique(labels)),
            'class_distribution': {
                int(label): int(count) 
                for label, count in zip(*np.unique(labels, return_counts=True))
            },
            'signal_mean': float(np.mean(signals)),
            'signal_std': float(np.std(signals)),
            'signal_min': float(np.min(signals)),
            'signal_max': float(np.max(signals))
        }
        
        # Check class balance
        counts = list(validation['stats']['class_distribution'].values())
        if max(counts) > 3 * min(counts):
            validation['warnings'].append(
                f"Significant class imbalance detected (ratio: {max(counts)/min(counts):.1f}:1)"
            )
        
        return validation
