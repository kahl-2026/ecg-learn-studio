"""Checkpoint Manager - Save and load model checkpoints"""

import json
import os
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


class CheckpointManager:
    """Manage model checkpoints and metadata."""
    
    def __init__(self, checkpoint_dir: str = 'checkpoints'):
        """
        Initialize checkpoint manager.
        
        Args:
            checkpoint_dir: Directory for storing checkpoints
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def save_checkpoint(
        self,
        model,
        model_type: str,
        metrics: Dict,
        metadata: Optional[Dict] = None,
        name: Optional[str] = None
    ) -> str:
        """
        Save model checkpoint with metadata.
        
        Args:
            model: Model instance
            model_type: Type of model
            metrics: Performance metrics
            metadata: Additional metadata
            name: Optional checkpoint name (default: auto-generated)
            
        Returns:
            Path to saved checkpoint
        """
        if name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"{model_type}_{timestamp}"
        
        checkpoint_path = self.checkpoint_dir / name
        checkpoint_path.mkdir(exist_ok=True)
        
        # Save model
        model_file = checkpoint_path / f"model.{self._get_extension(model_type)}"
        model.save(str(model_file))
        
        # Save metadata
        checkpoint_info = {
            'model_type': model_type,
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'metadata': metadata or {}
        }
        
        with open(checkpoint_path / 'checkpoint_info.json', 'w') as f:
            json.dump(checkpoint_info, f, indent=2)
        
        print(f"Checkpoint saved to {checkpoint_path}")
        return str(checkpoint_path)
    
    def load_checkpoint(self, name: str, model_class):
        """
        Load model from checkpoint.
        
        Args:
            name: Checkpoint name
            model_class: Model class to instantiate
            
        Returns:
            Loaded model and metadata
        """
        checkpoint_path = self.checkpoint_dir / name
        
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
        
        # Load metadata
        with open(checkpoint_path / 'checkpoint_info.json', 'r') as f:
            info = json.load(f)
        
        # Load model
        model_type = info['model_type']
        model_file = checkpoint_path / f"model.{self._get_extension(model_type)}"
        
        # Create model instance and load weights
        model = model_class
        model.load(str(model_file))
        
        return model, info
    
    def list_checkpoints(self) -> list:
        """
        List all available checkpoints.
        
        Returns:
            List of checkpoint info dictionaries
        """
        checkpoints = []
        
        for checkpoint_dir in self.checkpoint_dir.iterdir():
            if checkpoint_dir.is_dir():
                info_file = checkpoint_dir / 'checkpoint_info.json'
                if info_file.exists():
                    with open(info_file, 'r') as f:
                        info = json.load(f)
                    info['name'] = checkpoint_dir.name
                    checkpoints.append(info)
        
        # Sort by timestamp (newest first)
        checkpoints.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return checkpoints
    
    def delete_checkpoint(self, name: str):
        """Delete a checkpoint."""
        checkpoint_path = self.checkpoint_dir / name
        if checkpoint_path.exists():
            import shutil
            shutil.rmtree(checkpoint_path)
            print(f"Deleted checkpoint: {name}")
        else:
            raise FileNotFoundError(f"Checkpoint not found: {name}")
    
    def _get_extension(self, model_type: str) -> str:
        """Get file extension for model type."""
        if model_type in ['logistic', 'random_forest']:
            return 'pkl'
        elif model_type == 'cnn':
            return 'pth'
        else:
            return 'model'
