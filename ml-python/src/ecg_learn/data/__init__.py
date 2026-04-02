"""Data module - ECG data loading, generation, and management."""

__all__ = ["ECGDataLoader", "SyntheticECGGenerator"]


def __getattr__(name: str):
    # Keep package imports light so `python -m ecg_learn.data.synthetic` does not
    # preload synthetic via package import and trigger runpy warnings.
    if name == "ECGDataLoader":
        from .loader import ECGDataLoader

        return ECGDataLoader
    if name == "SyntheticECGGenerator":
        from .synthetic import SyntheticECGGenerator

        return SyntheticECGGenerator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
