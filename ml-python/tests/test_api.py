"""Test API handlers."""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ecg_learn.api.handlers import RequestHandler


class TestRequestHandler:
    """Test the API request handler."""
    
    @pytest.fixture
    def handler(self):
        """Create a fresh handler for each test."""
        return RequestHandler()
    
    def test_ping(self, handler):
        """Test ping health check."""
        result = handler.handle('ping', {})
        
        assert result['status'] == 'ok'
        assert 'backend_version' in result
        assert 'python_version' in result
    
    def test_load_synthetic_data(self, handler):
        """Test loading synthetic ECG data."""
        result = handler.handle('load_data', {
            'dataset_type': 'synthetic',
            'count': 50
        })
        
        assert 'dataset_id' in result
        assert 'signals' in result
        assert 'labels' in result
        assert 'sample_count' in result
        assert result['sample_count'] > 0
    
    def test_preprocess_signal(self, handler):
        """Test signal preprocessing."""
        # Generate a simple test signal
        signal = np.sin(np.linspace(0, 10*np.pi, 360)).tolist()
        
        result = handler.handle('preprocess', {
            'signal': signal,
            'sample_rate': 360,
            'config': {
                'bandpass': True,
                'remove_baseline': False,
                'notch_filter': False,
                'normalize': 'zscore'
            }
        })
        
        assert 'signal' in result
        assert len(result['signal']) == len(signal)
        assert 'preprocessing_applied' in result
    
    def test_extract_features(self, handler):
        """Test feature extraction."""
        # Generate a test signal
        signal = np.sin(np.linspace(0, 10*np.pi, 360)).tolist()
        
        result = handler.handle('extract_features', {
            'signal': signal,
            'sample_rate': 360
        })
        
        assert 'features' in result
        assert 'feature_names' in result
        assert 'feature_count' in result
        assert result['feature_count'] > 0
        
        # Check that standard features exist
        features = result['features']
        assert 'mean' in features
        assert 'std' in features
    
    def test_get_lessons(self, handler):
        """Test retrieving lesson list."""
        result = handler.handle('get_lessons', {})
        
        assert 'lessons' in result
        assert 'categories' in result
        assert len(result['lessons']) > 0
    
    def test_get_lesson_content(self, handler):
        """Test retrieving specific lesson content."""
        # First get list of lessons
        lessons_result = handler.handle('get_lessons', {})
        if len(lessons_result['lessons']) > 0:
            lesson_id = lessons_result['lessons'][0]['id']
            
            result = handler.handle('get_lesson_content', {
                'lesson_id': lesson_id,
                'difficulty': 'beginner'
            })
            
            assert 'title' in result
            assert 'content' in result
    
    def test_get_quiz_questions(self, handler):
        """Test retrieving quiz questions."""
        result = handler.handle('get_quiz_questions', {
            'count': 5
        })
        
        assert 'questions' in result
        assert 'categories' in result
    
    def test_train_model_logistic(self, handler):
        """Test training a logistic regression model."""
        result = handler.handle('train_model', {
            'model_type': 'logistic',
            'dataset_type': 'synthetic',
            'epochs': 1,
            'train_split': 0.8
        })
        
        assert 'model_id' in result
        assert 'accuracy' in result
        assert 'precision' in result
        assert 'recall' in result
        assert 'f1_score' in result
        assert 'confusion_matrix' in result
        assert result['accuracy'] >= 0.0
        assert result['accuracy'] <= 1.0
    
    def test_train_model_random_forest(self, handler):
        """Test training a random forest model."""
        result = handler.handle('train_model', {
            'model_type': 'random_forest',
            'dataset_type': 'synthetic',
            'train_split': 0.8
        })
        
        assert 'model_id' in result
        assert 'accuracy' in result
        assert result['accuracy'] >= 0.0
    
    def test_get_model_info(self, handler):
        """Test getting model info."""
        # Train a model first
        handler.handle('train_model', {
            'model_type': 'logistic',
            'dataset_type': 'synthetic'
        })
        
        result = handler.handle('get_model_info', {})
        
        assert 'available_models' in result
        assert len(result['available_models']) > 0

    def test_predict_without_trained_model_raises(self, handler):
        """Predict should fail fast when no model has been trained."""
        signal = np.sin(np.linspace(0, 10 * np.pi, 360)).tolist()
        with pytest.raises(ValueError, match="No trained model available"):
            handler.handle('predict', {'signal': signal})
    
    def test_unknown_method(self, handler):
        """Test that unknown methods raise an error."""
        with pytest.raises(ValueError, match="Unknown method"):
            handler.handle('nonexistent_method', {})


class TestDataLoadingIntegration:
    """Test data loading integration."""
    
    @pytest.fixture
    def handler(self):
        return RequestHandler()
    
    def test_load_then_train(self, handler):
        """Test loading data then training a model."""
        # Load data
        load_result = handler.handle('load_data', {
            'dataset_type': 'synthetic',
            'count': 100
        })
        
        assert 'dataset_id' in load_result
        
        # Train model (will use synthetic data)
        train_result = handler.handle('train_model', {
            'model_type': 'logistic',
            'dataset_type': 'synthetic'
        })
        
        assert 'model_id' in train_result
        assert train_result['accuracy'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
