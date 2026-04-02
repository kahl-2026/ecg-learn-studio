"""Integration tests for the ECG Learn Studio system."""

import pytest
import subprocess
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


class TestPythonBackendIntegration:
    """Test the Python backend as it would be called from Rust."""
    
    def test_api_server_starts(self):
        """Test that the API server can start and respond to ping."""
        from ecg_learn.api.handlers import RequestHandler
        
        handler = RequestHandler()
        result = handler.handle('ping', {})
        
        assert result['status'] == 'ok'
    
    def test_full_training_pipeline(self):
        """Test the complete training pipeline end-to-end."""
        from ecg_learn.api.handlers import RequestHandler
        
        handler = RequestHandler()
        
        # 1. Load synthetic data
        data_result = handler.handle('load_data', {
            'dataset_type': 'synthetic',
            'count': 100
        })
        assert 'dataset_id' in data_result
        
        # 2. Train model
        train_result = handler.handle('train_model', {
            'model_type': 'logistic',
            'dataset_type': 'synthetic',
            'train_split': 0.8
        })
        assert 'model_id' in train_result
        assert train_result['accuracy'] > 0
        
        # 3. Get model info
        model_info = handler.handle('get_model_info', {})
        assert 'available_models' in model_info
        assert len(model_info['available_models']) > 0
    
    def test_full_prediction_pipeline(self):
        """Test prediction workflow."""
        from ecg_learn.api.handlers import RequestHandler
        from ecg_learn.data import SyntheticECGGenerator
        
        handler = RequestHandler()
        
        # 1. Train a model
        handler.handle('train_model', {
            'model_type': 'logistic',
            'dataset_type': 'synthetic'
        })
        
        # 2. Generate a test signal
        gen = SyntheticECGGenerator(seed=42)
        test_signal = gen.generate_normal_sinus().tolist()
        
        # 3. Make prediction
        pred_result = handler.handle('predict', {
            'signal': test_signal
        })
        
        assert 'predicted_class' in pred_result
        assert 'confidence' in pred_result
        assert pred_result['confidence'] >= 0
        assert pred_result['confidence'] <= 1
        
        # 4. Get explanation
        explain_result = handler.handle('explain', {
            'predicted_class': pred_result['predicted_class'],
            'confidence': pred_result['confidence']
        })
        
        assert 'explanation' in explain_result
    
    def test_quiz_workflow(self):
        """Test complete quiz workflow."""
        from ecg_learn.api.handlers import RequestHandler
        
        handler = RequestHandler()
        
        # 1. Get questions
        questions = handler.handle('get_quiz_questions', {
            'count': 5
        })
        
        assert 'questions' in questions
        assert len(questions['questions']) > 0
        
        # 2. Submit an answer (just testing the flow, not correctness)
        if len(questions['questions']) > 0:
            question = questions['questions'][0]
            
            result = handler.handle('submit_quiz_answer', {
                'question_id': question['id'],
                'answer': 0  # First option
            })
            
            assert 'correct' in result
            
            # 3. Check progress
            progress = handler.handle('get_quiz_progress', {})
            assert 'statistics' in progress
    
    def test_lesson_workflow(self):
        """Test lesson retrieval workflow."""
        from ecg_learn.api.handlers import RequestHandler
        
        handler = RequestHandler()
        
        # 1. Get all lessons
        lessons = handler.handle('get_lessons', {})
        
        assert 'lessons' in lessons
        assert len(lessons['lessons']) > 0
        
        # 2. Get specific lesson content
        if len(lessons['lessons']) > 0:
            lesson_id = lessons['lessons'][0]['id']
            
            content = handler.handle('get_lesson_content', {
                'lesson_id': lesson_id,
                'difficulty': 'beginner'
            })
            
            assert 'title' in content
            assert 'content' in content


class TestDataPipeline:
    """Test data processing pipeline."""
    
    def test_preprocess_then_extract_features(self):
        """Test preprocessing followed by feature extraction."""
        from ecg_learn.api.handlers import RequestHandler
        from ecg_learn.data import SyntheticECGGenerator
        
        handler = RequestHandler()
        gen = SyntheticECGGenerator(seed=42)
        
        # Generate raw signal
        raw_signal = gen.generate_normal_sinus().tolist()
        
        # Preprocess
        preprocessed = handler.handle('preprocess', {
            'signal': raw_signal,
            'sample_rate': 360,
            'config': {
                'bandpass': True,
                'normalize': 'zscore'
            }
        })
        
        assert len(preprocessed['signal']) == len(raw_signal)
        
        # Extract features
        features = handler.handle('extract_features', {
            'signal': preprocessed['signal'],
            'sample_rate': 360
        })
        
        assert features['feature_count'] > 0


class TestModelComparison:
    """Test comparing different model types."""
    
    def test_compare_baseline_models(self):
        """Compare logistic regression and random forest."""
        from ecg_learn.api.handlers import RequestHandler
        
        handler = RequestHandler()
        
        # Train logistic
        logistic_result = handler.handle('train_model', {
            'model_type': 'logistic',
            'dataset_type': 'synthetic'
        })
        
        # Train random forest
        rf_result = handler.handle('train_model', {
            'model_type': 'random_forest',
            'dataset_type': 'synthetic'
        })
        
        # Both should produce valid metrics
        assert logistic_result['accuracy'] > 0
        assert rf_result['accuracy'] > 0
        assert logistic_result['f1_score'] > 0
        assert rf_result['f1_score'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
