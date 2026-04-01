"""Data module - ECG data loading, generation, and management"""

from .loader import ECGDataLoader
from .synthetic import SyntheticECGGenerator

__all__ = ['ECGDataLoader', 'SyntheticECGGenerator']
