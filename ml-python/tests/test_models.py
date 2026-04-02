"""Test ML models."""

import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ecg_learn.models import ModelRegistry
from ecg_learn.models.baseline import BaselineModels
from ecg_learn.data import SyntheticECGGenerator
from ecg_learn.preprocessing import ECGFeatureExtractor


class TestModelRegistry:
    """Test the model registry."""
    
    def test_list_models(self):
        """Test listing available models."""
        models = ModelRegistry.list_models()
        
        assert 'logistic' in models
        assert 'random_forest' in models
        assert 'cnn' in models
    
    def test_create_logistic(self):
        """Test creating logistic regression model."""
        model = ModelRegistry.create_model('logistic')
        
        assert model is not None
        assert model.model_type == 'logistic'
    
    def test_create_random_forest(self):
        """Test creating random forest model."""
        model = ModelRegistry.create_model('random_forest')
        
        assert model is not None
        assert model.model_type == 'random_forest'
    
    def test_create_cnn(self):
        """Test creating CNN model."""
        model = ModelRegistry.create_model('cnn')
        
        assert model is not None
    
    def test_create_unknown_model(self):
        """Test that unknown model type raises error."""
        with pytest.raises(ValueError, match="Unknown model type"):
            ModelRegistry.create_model('nonexistent')
    
    def test_get_model_info(self):
        """Test getting model info."""
        info = ModelRegistry.get_model_info('logistic')
        
        assert 'name' in info
        assert 'description' in info
        assert 'requires_features' in info
    
    def test_get_default_hyperparameters(self):
        """Test getting default hyperparameters."""
        params = ModelRegistry.get_default_hyperparameters('cnn')
        
        assert 'epochs' in params
        assert 'learning_rate' in params


class TestBaselineModels:
    """Test baseline ML models."""
    
    @pytest.fixture
    def sample_data(self):
        """Generate sample training data."""
        gen = SyntheticECGGenerator(seed=42)
        signals, labels, label_names = gen.generate_dataset(n_samples_per_class=50)
        
        # Extract features
        extractor = ECGFeatureExtractor()
        features = extractor.extract_dataset(signals)
        
        return features, labels, label_names
    
    def test_logistic_train(self, sample_data):
        """Test logistic regression training."""
        X, y, _ = sample_data
        model = BaselineModels('logistic')
        
        result = model.train(X, y)
        
        assert model.is_trained
        assert 'train_accuracy' in result
        assert result['train_accuracy'] > 0
    
    def test_logistic_predict(self, sample_data):
        """Test logistic regression prediction."""
        X, y, _ = sample_data
        model = BaselineModels('logistic')
        model.train(X, y)
        
        predictions = model.predict(X[:10])
        
        assert len(predictions) == 10
        assert all(p in np.unique(y) for p in predictions)
    
    def test_logistic_predict_proba(self, sample_data):
        """Test logistic regression probability prediction."""
        X, y, _ = sample_data
        model = BaselineModels('logistic')
        model.train(X, y)
        
        probas = model.predict_proba(X[:10])
        
        assert probas.shape == (10, len(np.unique(y)))
        # Probabilities should sum to 1
        np.testing.assert_array_almost_equal(probas.sum(axis=1), np.ones(10))
    
    def test_random_forest_train(self, sample_data):
        """Test random forest training."""
        X, y, _ = sample_data
        model = BaselineModels('random_forest')
        
        result = model.train(X, y)
        
        assert model.is_trained
        assert 'train_accuracy' in result
    
    def test_random_forest_predict(self, sample_data):
        """Test random forest prediction."""
        X, y, _ = sample_data
        model = BaselineModels('random_forest')
        model.train(X, y)
        
        predictions = model.predict(X[:10])
        
        assert len(predictions) == 10
    
    def test_feature_importance(self, sample_data):
        """Test feature importance extraction."""
        X, y, _ = sample_data
        model = BaselineModels('random_forest')
        model.train(X, y)
        
        importance = model.get_feature_importance()
        
        assert isinstance(importance, dict)
        assert len(importance) > 0
    
    def test_predict_before_train_raises(self, sample_data):
        """Test that predicting before training raises error."""
        X, _, _ = sample_data
        model = BaselineModels('logistic')
        
        with pytest.raises(ValueError, match="not trained"):
            model.predict(X)
    
    def test_class_weights(self, sample_data):
        """Test training with class weights."""
        X, y, _ = sample_data
        model = BaselineModels('logistic')
        
        # Train with balanced class weights
        result = model.train(X, y, class_weights='balanced')
        
        assert model.is_trained


class TestModelPersistence:
    """Test model saving and loading."""
    
    @pytest.fixture
    def sample_data(self):
        gen = SyntheticECGGenerator(seed=42)
        signals, labels, _ = gen.generate_dataset(n_samples_per_class=20)
        extractor = ECGFeatureExtractor()
        return extractor.extract_dataset(signals), labels
    
    def test_save_load_logistic(self, sample_data, tmp_path):
        """Test saving and loading logistic model."""
        X, y = sample_data
        model = BaselineModels('logistic')
        model.train(X, y)
        
        # Save model
        save_path = tmp_path / 'logistic_model.pkl'
        model.save(str(save_path))
        
        assert save_path.exists()
        
        # Load and verify
        loaded_model = BaselineModels('logistic')
        loaded_model.load(str(save_path))
        
        assert loaded_model.is_trained
        
        # Predictions should match
        orig_pred = model.predict(X[:5])
        loaded_pred = loaded_model.predict(X[:5])
        np.testing.assert_array_equal(orig_pred, loaded_pred)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
