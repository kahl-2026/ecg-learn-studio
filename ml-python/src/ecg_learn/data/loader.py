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
    
    def load_dataset(self, dataset_type: str, **kwargs) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Load a dataset by type.
        
        Args:
            dataset_type: 'synthetic', 'mitbih', or 'ptbxl'
            **kwargs: Dataset-specific arguments
            
        Returns:
            signals, labels, label_names
        """
        if dataset_type == 'synthetic':
            return self.load_synthetic()
        elif dataset_type == 'mitbih':
            return self.load_mitbih(**kwargs)
        elif dataset_type == 'ptbxl':
            return self.load_ptbxl(**kwargs)
        else:
            raise ValueError(f"Unknown dataset type: {dataset_type}")
    
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
        
        # Standard MIT-BIH records
        default_records = [
            '100', '101', '102', '103', '104', '105', '106', '107', '108', '109',
            '111', '112', '113', '114', '115', '116', '117', '118', '119', '121',
            '122', '123', '124', '200', '201', '202', '203', '205', '207', '208',
            '209', '210', '212', '213', '214', '215', '217', '219', '220', '221',
            '222', '223', '228', '230', '231', '232', '233', '234'
        ]
        
        records_to_load = records or default_records
        
        # AAMI beat class mapping (5 classes like in standard benchmarks)
        aami_classes = {
            'N': 0,  # Normal beat
            'L': 0,  # Left bundle branch block
            'R': 0,  # Right bundle branch block
            'e': 0,  # Atrial escape
            'j': 0,  # Nodal (junctional) escape
            
            'A': 1,  # Atrial premature (SVEB)
            'a': 1,  # Aberrated atrial premature
            'S': 1,  # Supraventricular premature
            'J': 1,  # Nodal (junctional) premature
            
            'V': 2,  # Premature ventricular contraction (VEB)
            'E': 2,  # Ventricular escape
            
            'F': 3,  # Fusion of ventricular and normal
            
            '/': 4,  # Paced beat
            'f': 4,  # Fusion of paced and normal
        }
        
        label_names = ['Normal', 'SVEB', 'VEB', 'Fusion', 'Unknown']
        
        signals_list = []
        labels_list = []
        segment_length = 360  # 1 second at 360 Hz
        half_segment = segment_length // 2
        
        for record_name in records_to_load:
            record_path = mitbih_dir / record_name
            
            # Check if record exists
            if not (record_path.with_suffix('.dat')).exists():
                continue
            
            try:
                # Load record
                record = wfdb.rdrecord(str(record_path))
                annotation = wfdb.rdann(str(record_path), 'atr')
                
                # Get first lead signal
                signal = record.p_signal[:, 0]
                
                # Extract beats
                for i, (sample, symbol) in enumerate(zip(annotation.sample, annotation.symbol)):
                    if symbol not in aami_classes:
                        continue
                    
                    # Extract segment centered on beat
                    start = sample - half_segment
                    end = sample + half_segment
                    
                    if start < 0 or end > len(signal):
                        continue
                    
                    segment = signal[start:end]
                    
                    if len(segment) == segment_length:
                        signals_list.append(segment)
                        labels_list.append(aami_classes[symbol])
                        
            except Exception as e:
                print(f"Warning: Could not load record {record_name}: {e}")
                continue
        
        if len(signals_list) == 0:
            raise ValueError("No beats extracted from MIT-BIH dataset")
        
        signals = np.array(signals_list)
        labels = np.array(labels_list)
        
        print(f"Loaded MIT-BIH dataset: {signals.shape[0]} beats, {len(label_names)} classes")
        
        return signals, labels, label_names
    
    def load_ptbxl(self, sampling_rate: int = 100, lead: int = 0) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Load PTB-XL Database.
        
        Args:
            sampling_rate: 100 or 500 Hz
            lead: Which lead to use (0-11 for 12-lead ECG, default lead I)
            
        Returns:
            signals: ECG signals
            labels: Diagnostic labels
            label_names: Diagnosis names
        """
        ptbxl_dir = self.base_dir / 'ptbxl'
        
        if not ptbxl_dir.exists():
            raise FileNotFoundError(
                f"PTB-XL dataset not found in {ptbxl_dir}. "
                "Run: make download-datasets"
            )
        
        try:
            import pandas as pd
            import wfdb
            import ast
        except ImportError:
            raise ImportError("pandas and wfdb packages required")
        
        # Load metadata
        metadata_path = ptbxl_dir / 'ptbxl_database.csv'
        if not metadata_path.exists():
            raise FileNotFoundError(f"PTB-XL metadata file not found: {metadata_path}")
        
        df = pd.read_csv(metadata_path, index_col='ecg_id')
        
        # Parse the scp_codes column
        df['scp_codes'] = df['scp_codes'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else {})
        
        # Define simplified diagnostic classes (for 5-class classification)
        # Based on PTB-XL paper categories
        diagnostic_classes = {
            'NORM': 0,  # Normal
            'MI': 1,    # Myocardial Infarction
            'STTC': 2,  # ST/T Change
            'CD': 3,    # Conduction Disturbance
            'HYP': 4,   # Hypertrophy
        }
        
        label_names = ['Normal', 'MI', 'ST/T Change', 'Conduction Dist.', 'Hypertrophy']
        
        # Load diagnostic superclass mapping
        scp_statements_path = ptbxl_dir / 'scp_statements.csv'
        if scp_statements_path.exists():
            scp_df = pd.read_csv(scp_statements_path, index_col=0)
            # Map each SCP code to a diagnostic superclass
            code_to_class = {}
            for code in scp_df.index:
                if 'diagnostic_class' in scp_df.columns:
                    diag_class = scp_df.loc[code, 'diagnostic_class']
                    if pd.notna(diag_class) and diag_class in diagnostic_classes:
                        code_to_class[code] = diagnostic_classes[diag_class]
        else:
            code_to_class = {}
        
        signals_list = []
        labels_list = []
        
        # Determine which path column to use
        if sampling_rate == 500:
            path_col = 'filename_hr'  # high resolution
        else:
            path_col = 'filename_lr'  # low resolution (100 Hz)
        
        # Load signals
        for idx, row in df.iterrows():
            # Get the primary diagnosis
            scp_codes = row['scp_codes']
            
            # Find highest confidence diagnosis
            primary_label = None
            max_confidence = 0
            for code, confidence in scp_codes.items():
                if code in code_to_class and confidence > max_confidence:
                    primary_label = code_to_class[code]
                    max_confidence = confidence
            
            if primary_label is None:
                continue  # Skip records without clear diagnosis
            
            # Load signal
            try:
                signal_path = ptbxl_dir / row[path_col]
                record = wfdb.rdrecord(str(signal_path).replace('.dat', ''))
                signal = record.p_signal[:, lead]  # Use specified lead
                
                # Ensure consistent length
                expected_length = 10 * sampling_rate  # 10 seconds
                if len(signal) >= expected_length:
                    signal = signal[:expected_length]
                else:
                    # Pad with zeros if needed
                    signal = np.pad(signal, (0, expected_length - len(signal)))
                
                signals_list.append(signal)
                labels_list.append(primary_label)
                
            except Exception as e:
                continue
        
        if len(signals_list) == 0:
            raise ValueError("No signals loaded from PTB-XL dataset")
        
        signals = np.array(signals_list)
        labels = np.array(labels_list)
        
        print(f"Loaded PTB-XL dataset: {signals.shape[0]} records, {len(label_names)} classes")
        
        return signals, labels, label_names
    
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
