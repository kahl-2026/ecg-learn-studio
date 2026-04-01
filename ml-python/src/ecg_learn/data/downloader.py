"""Dataset downloader for MIT-BIH and PTB-XL ECG datasets"""

import os
import requests
from pathlib import Path
from typing import Optional
from tqdm import tqdm
import hashlib


class ECGDatasetDownloader:
    """Download public ECG datasets from PhysioNet."""
    
    DATASETS = {
        'mitbih': {
            'url': 'https://physionet.org/static/published-projects/mitdb/mit-bih-arrhythmia-database-1.0.0.zip',
            'checksum': None,  # Optional MD5 checksum
            'description': 'MIT-BIH Arrhythmia Database'
        },
        'ptbxl': {
            'url': 'https://physionet.org/static/published-projects/ptb-xl/ptb-xl-a-large-publicly-available-electrocardiography-dataset-1.0.3.zip',
            'checksum': None,
            'description': 'PTB-XL ECG Database'
        }
    }
    
    def __init__(self, base_dir: str = '../datasets'):
        """
        Initialize downloader.
        
        Args:
            base_dir: Base directory for storing datasets
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def download(self, dataset_name: str, force: bool = False) -> Path:
        """
        Download a dataset.
        
        Args:
            dataset_name: 'mitbih' or 'ptbxl'
            force: Re-download even if exists
            
        Returns:
            Path to downloaded dataset directory
        """
        if dataset_name not in self.DATASETS:
            raise ValueError(f"Unknown dataset: {dataset_name}. Available: {list(self.DATASETS.keys())}")
        
        dataset_info = self.DATASETS[dataset_name]
        dataset_dir = self.base_dir / dataset_name
        
        if dataset_dir.exists() and not force:
            print(f"{dataset_name} already exists in {dataset_dir}")
            return dataset_dir
        
        dataset_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Downloading {dataset_info['description']}...")
        print(f"URL: {dataset_info['url']}")
        print(f"Destination: {dataset_dir}")
        
        zip_path = dataset_dir / f"{dataset_name}.zip"
        
        try:
            self._download_file(dataset_info['url'], zip_path)
            
            if dataset_info['checksum']:
                if not self._verify_checksum(zip_path, dataset_info['checksum']):
                    raise ValueError("Checksum verification failed")
            
            print("Extracting...")
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(dataset_dir)
            
            # Clean up zip file
            zip_path.unlink()
            
            print(f"✓ Successfully downloaded {dataset_name} to {dataset_dir}")
            return dataset_dir
            
        except Exception as e:
            print(f"✗ Download failed: {e}")
            raise
    
    def _download_file(self, url: str, dest: Path):
        """Download file with progress bar."""
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(dest, 'wb') as f, tqdm(
            total=total_size,
            unit='B',
            unit_scale=True,
            desc=dest.name
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                pbar.update(len(chunk))
    
    def _verify_checksum(self, file_path: Path, expected_md5: str) -> bool:
        """Verify file MD5 checksum."""
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                md5.update(chunk)
        return md5.hexdigest() == expected_md5
    
    def list_available(self):
        """List available datasets."""
        print("Available datasets:")
        for name, info in self.DATASETS.items():
            exists = "✓ Downloaded" if (self.base_dir / name).exists() else "  Not downloaded"
            print(f"  {name:10s} - {info['description']:50s} [{exists}]")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Download ECG datasets')
    parser.add_argument('--dataset', choices=['mitbih', 'ptbxl', 'all'], default='all')
    parser.add_argument('--output', default='../datasets/')
    parser.add_argument('--force', action='store_true', help='Force re-download')
    args = parser.parse_args()
    
    downloader = ECGDatasetDownloader(args.output)
    
    if args.dataset == 'all':
        downloader.list_available()
        print("\nTo download datasets, use: --dataset mitbih or --dataset ptbxl")
        print("Note: PTB-XL is ~500MB, MIT-BIH is ~50MB")
    else:
        downloader.download(args.dataset, force=args.force)
