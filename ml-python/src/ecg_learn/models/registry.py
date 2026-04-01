"""Model Registry - Factory pattern for creating and managing models"""

from typing import Dict, Any, Optional
from .baseline import BaselineModels
from .cnn import ECGCNNWrapper


class ModelRegistry:
    """Registry for creating and managing ML models."""
    
    AVAILABLE_MODELS = {
        'logistic': {
            'name': 'Logistic Regression',
            'type': 'baseline',
            'description': 'Fast linear classifier, interpretable feature importance',
            'requires_features': True
        },
        'random_forest': {
            'name': 'Random Forest',
            'type': 'baseline',
            'description': 'Ensemble of decision trees, robust to overfitting',
            'requires_features': True
        },
        'cnn': {
            'name': '1D CNN',
            'type': 'neural',
            'description': 'Deep learning on raw signals, learns features automatically',
            'requires_features': False
        }
    }
    
    @staticmethod
    def create_model(model_type: str, **kwargs) -> Any:
        """
        Create a model instance.
        
        Args:
            model_type: Type of model ('logistic', 'random_forest', 'cnn')
            **kwargs: Model-specific parameters
            
        Returns:
            Model instance
        """
        if model_type not in ModelRegistry.AVAILABLE_MODELS:
            raise ValueError(
                f"Unknown model type: {model_type}. "
                f"Available: {list(ModelRegistry.AVAILABLE_MODELS.keys())}"
            )
        
        model_info = ModelRegistry.AVAILABLE_MODELS[model_type]
        
        if model_info['type'] == 'baseline':
            return BaselineModels(model_type=model_type, **kwargs)
        elif model_info['type'] == 'neural':
            return ECGCNNWrapper(**kwargs)
        else:
            raise ValueError(f"Unknown model category: {model_info['type']}")
    
    @staticmethod
    def get_model_info(model_type: str) -> Dict:
        """Get information about a model type."""
        if model_type not in ModelRegistry.AVAILABLE_MODELS:
            raise ValueError(f"Unknown model type: {model_type}")
        
        return ModelRegistry.AVAILABLE_MODELS[model_type].copy()
    
    @staticmethod
    def list_models() -> Dict:
        """List all available models."""
        return {
            model_type: {
                'name': info['name'],
                'description': info['description'],
                'requires_features': info['requires_features']
            }
            for model_type, info in ModelRegistry.AVAILABLE_MODELS.items()
        }
    
    @staticmethod
    def get_default_hyperparameters(model_type: str) -> Dict:
        """Get default hyperparameters for a model type."""
        defaults = {
            'logistic': {
                'random_state': 42,
                'max_iter': 1000,
                'C': 1.0
            },
            'random_forest': {
                'random_state': 42,
                'n_estimators': 100,
                'max_depth': 10,
                'min_samples_split': 5
            },
            'cnn': {
                'input_length': 3600,
                'n_classes': 5,
                'n_channels': 32,
                'learning_rate': 0.001,
                'batch_size': 32,
                'epochs': 50
            }
        }
        
        return defaults.get(model_type, {})
