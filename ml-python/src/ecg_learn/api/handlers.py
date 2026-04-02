"""Request Handlers - Process API method calls"""

import numpy as np
from typing import Dict, Any, List, Optional
from ..data import SyntheticECGGenerator, ECGDataLoader
from ..preprocessing import ECGFilters, ECGSegmentation, ECGFeatureExtractor
from ..models import ModelRegistry
from ..training import ModelTrainer, ModelEvaluator, CheckpointManager
from ..inference import ECGPredictor, PredictionExplainer
from ..education import LessonManager, ECGGlossary
from ..quiz import QuizQuestionBank, QuizProgressTracker


class RequestHandler:
    """Handle all API method requests."""
    
    def __init__(self):
        """Initialize handlers and state."""
        self.datasets = {}
        self.models = {}
        self.lesson_manager = LessonManager()
        self.glossary = ECGGlossary()
        self.quiz_bank = QuizQuestionBank()
        self.quiz_tracker = QuizProgressTracker()
        self.checkpoint_manager = CheckpointManager()
        self.filters = ECGFilters()
        self.feature_extractor = ECGFeatureExtractor()
    
    def handle(self, method: str, params: Dict[str, Any]) -> Dict:
        """
        Route method to appropriate handler.
        
        Args:
            method: API method name
            params: Method parameters
            
        Returns:
            Result dictionary
        """
        handlers = {
            'ping': self.ping,
            'load_data': self.load_data,
            'get_datasets': self.get_datasets,
            'preprocess': self.preprocess,
            'extract_features': self.extract_features,
            'train_model': self.train_model,
            'get_model_info': self.get_model_info,
            'predict': self.predict,
            'explain': self.explain,
            'get_lessons': self.get_lessons,
            'get_lesson_content': self.get_lesson_content,
            'get_glossary': self.get_glossary,
            'get_quiz_questions': self.get_quiz_questions,
            'submit_quiz_answer': self.submit_quiz_answer,
            'get_quiz_progress': self.get_quiz_progress
        }
        
        handler = handlers.get(method)
        if not handler:
            raise ValueError(f"Unknown method: {method}")
        
        return handler(params)
    
    def ping(self, params: Dict) -> Dict:
        """Health check."""
        import sys
        return {
            'status': 'ok',
            'backend_version': '1.0.0',
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        }
    
    def load_data(self, params: Dict) -> Dict:
        """Load or generate dataset."""
        dataset_type = params.get('dataset_type', 'synthetic')
        count = params.get('count', 100)
        
        if dataset_type == 'synthetic':
            generator = SyntheticECGGenerator()
            signals, labels, label_names = generator.generate_dataset(
                n_samples_per_class=max(count // 5, 5)
            )
            
            dataset_id = f"synthetic_{len(self.datasets)}"
            self.datasets[dataset_id] = {
                'signals': signals,
                'labels': labels,
                'label_names': label_names,
                'type': 'synthetic',
                'sample_rate': 360
            }
            
            # Return signals as nested lists for JSON serialization
            signals_list = signals.tolist() if hasattr(signals, 'tolist') else list(signals)
            labels_list = [label_names[int(l)] for l in labels]
            
            return {
                'dataset_id': dataset_id,
                'signals': signals_list,
                'labels': labels_list,
                'sample_rate': 360,
                'sample_count': len(signals),
                'class_names': label_names
            }
        
        else:
            # For real datasets, try to load
            loader = ECGDataLoader()
            try:
                signals, labels, label_names = loader.load_dataset(dataset_type)
                if len(signals) == 0:
                    raise ValueError(f"Dataset {dataset_type} not found or empty. Run download-datasets.sh first.")
                
                dataset_id = f"{dataset_type}_{len(self.datasets)}"
                self.datasets[dataset_id] = {
                    'signals': signals,
                    'labels': labels,
                    'label_names': label_names,
                    'type': dataset_type,
                    'sample_rate': 360
                }
                
                signals_list = signals[:count].tolist() if hasattr(signals, 'tolist') else list(signals[:count])
                labels_list = [label_names[int(l)] for l in labels[:count]]
                
                return {
                    'dataset_id': dataset_id,
                    'signals': signals_list,
                    'labels': labels_list,
                    'sample_rate': 360,
                    'sample_count': len(signals_list),
                    'class_names': label_names
                }
            except Exception as e:
                raise ValueError(f"Failed to load {dataset_type}: {str(e)}")
    
    def get_datasets(self, params: Dict) -> Dict:
        """List loaded datasets."""
        return {
            'datasets': [
                {
                    'id': ds_id,
                    'type': ds_data['type'],
                    'sample_count': len(ds_data['signals'])
                }
                for ds_id, ds_data in self.datasets.items()
            ]
        }
    
    def preprocess(self, params: Dict) -> Dict:
        """Preprocess signal data with filtering and normalization."""
        sig = np.array(params.get('signal', []))
        sample_rate = params.get('sample_rate', 360)
        
        # Create filter with correct sample rate
        filters = ECGFilters(sampling_rate=sample_rate)
        
        # Apply preprocessing pipeline
        config = params.get('config', {})
        
        # Bandpass filter
        if config.get('bandpass', True):
            low_freq = config.get('low_freq', 0.5)
            high_freq = config.get('high_freq', 40.0)
            sig = filters.bandpass_filter(sig, lowcut=low_freq, highcut=high_freq)
        
        # Remove baseline wander
        if config.get('remove_baseline', True):
            cutoff = config.get('baseline_cutoff', 0.5)
            sig = filters.remove_baseline_wander(sig, cutoff=cutoff)
        
        # Notch filter for powerline interference
        if config.get('notch_filter', False):
            freq = config.get('notch_freq', 60.0)
            sig = filters.notch_filter(sig, freq=freq)
        
        # Normalize
        normalize_method = config.get('normalize', 'zscore')
        if normalize_method:
            sig, _ = filters.normalize(sig, method=normalize_method)
        
        return {
            'signal': sig.tolist() if hasattr(sig, 'tolist') else list(sig),
            'sample_rate': sample_rate,
            'preprocessing_applied': {
                'bandpass': config.get('bandpass', True),
                'remove_baseline': config.get('remove_baseline', True),
                'notch_filter': config.get('notch_filter', False),
                'normalize': normalize_method
            }
        }
    
    def extract_features(self, params: Dict) -> Dict:
        """Extract features from a signal for ML models."""
        sig = np.array(params.get('signal', []))
        sample_rate = params.get('sample_rate', 360)
        
        # Create extractor with correct sample rate
        extractor = ECGFeatureExtractor(sampling_rate=sample_rate)
        
        # Extract all feature types (r_peaks is optional, will be None if not provided)
        r_peaks = params.get('r_peaks')
        if r_peaks is not None:
            r_peaks = np.array(r_peaks)
        
        features = extractor.extract_all(sig, r_peaks=r_peaks, include_frequency=True)
        
        # Get feature names
        feature_names = list(features.keys())
        
        return {
            'features': features,
            'feature_names': feature_names,
            'feature_count': len(feature_names)
        }
    
    def train_model(self, params: Dict) -> Dict:
        """Train a model."""
        model_type = params.get('model_type', 'logistic')
        dataset_type = params.get('dataset_type', 'synthetic')
        epochs = params.get('epochs', 10)
        learning_rate = params.get('learning_rate', 0.001)
        train_split = params.get('train_split', 0.8)
        samples_per_class = int(params.get('samples_per_class', 40))
        
        # Load or generate data if needed
        if dataset_type == 'synthetic':
            generator = SyntheticECGGenerator()
            signals, labels, label_names = generator.generate_dataset(
                n_samples_per_class=max(samples_per_class, 10)
            )
        else:
            # Use first matching dataset or load fresh
            dataset_id = None
            for ds_id, ds_data in self.datasets.items():
                if ds_data['type'] == dataset_type:
                    dataset_id = ds_id
                    break
            
            if dataset_id:
                dataset = self.datasets[dataset_id]
                signals = dataset['signals']
                labels = dataset['labels']
                label_names = dataset['label_names']
            else:
                # Try to load
                loader = ECGDataLoader()
                signals, labels, label_names = loader.load_dataset(dataset_type)
                if len(signals) == 0:
                    # Fallback to synthetic
                    generator = SyntheticECGGenerator()
                    signals, labels, label_names = generator.generate_dataset(
                        n_samples_per_class=max(samples_per_class, 10)
                    )
        
        X = np.array(signals)
        y = np.array(labels)
        
        # Create model
        model = ModelRegistry.create_model(model_type)
        
        # For baseline models, extract features
        if model_type in ['logistic', 'random_forest']:
            X_features = self.feature_extractor.extract_dataset(X)
        else:
            X_features = X
        
        # Train/validation split
        from sklearn.model_selection import train_test_split
        X_train, X_val, y_train, y_val = train_test_split(
            X_features, y, train_size=train_split, random_state=42, stratify=y
        )
        
        # Train
        if model_type in ['logistic', 'random_forest']:
            # Pass class_weights as dict or 'balanced' string
            model.train(X_train, y_train, class_weights='balanced')
            y_pred = model.predict(X_val)
            y_prob = model.predict_proba(X_val)
        else:
            # CNN training - pass the whole training data since trainer handles splits
            trainer = ModelTrainer(model, model_type)
            # For CNN, X_train needs to be 2D (samples, signal_length) not feature matrix
            X_cnn = signals[:int(len(signals) * train_split)]
            y_cnn = labels[:int(len(labels) * train_split)]
            X_val_cnn = signals[int(len(signals) * train_split):]
            y_val_cnn = labels[int(len(labels) * train_split):]
            
            trainer.train_cnn(X_cnn, y_cnn, X_val_cnn, y_val_cnn, 
                            epochs=epochs, learning_rate=learning_rate)
            y_pred = model.predict(X_val_cnn)
            y_prob = model.predict_proba(X_val_cnn)
            # Use CNN validation data for evaluation
            y_val = y_val_cnn
        
        # Evaluate
        evaluator = ModelEvaluator(label_names)
        metrics = evaluator.evaluate(y_val, y_pred, y_prob)
        
        # Store model
        model_id = f"{model_type}_model_latest"
        self.models[model_id] = {
            'model': model,
            'model_type': model_type,
            'label_names': label_names,
            'metrics': metrics,
            'epochs': epochs
        }
        
        # Generate explanation
        explanation = evaluator.explain_metrics(metrics)
        
        # Extract metrics for response
        macro_avg = metrics.get('macro_avg', {})
        
        return {
            'model_id': model_id,
            'accuracy': metrics.get('accuracy', 0),
            'precision': macro_avg.get('precision', 0),
            'recall': macro_avg.get('recall', 0),
            'f1_score': macro_avg.get('f1', 0),
            'confusion_matrix': metrics.get('confusion_matrix', []),
            'class_names': label_names,
            'explanation': explanation
        }
    
    def get_model_info(self, params: Dict) -> Dict:
        """Get information about a trained model."""
        model_id = params.get('model_id')
        
        if model_id and model_id in self.models:
            model_info = self.models[model_id]
            return {
                'model_id': model_id,
                'model_type': model_info['model_type'],
                'label_names': model_info['label_names'],
                'metrics': model_info.get('metrics', {}),
                'epochs': model_info.get('epochs', 0)
            }
        
        # List all available models
        return {
            'available_models': [
                {
                    'model_id': mid,
                    'model_type': minfo['model_type'],
                    'accuracy': minfo.get('metrics', {}).get('accuracy', 0)
                }
                for mid, minfo in self.models.items()
            ]
        }
    
    def predict(self, params: Dict) -> Dict:
        """Make predictions."""
        model_id = params.get('model_id')
        signal = params.get('signal', params.get('data', []))
        
        # Use latest model when not specified, but do not auto-train on predict.
        if not model_id:
            if self.models:
                model_id = list(self.models.keys())[-1]
            else:
                raise ValueError(
                    "No trained model available. Train a model first in the Train screen."
                )
        elif model_id not in self.models:
            available = ", ".join(self.models.keys()) if self.models else "none"
            raise ValueError(
                f"Model '{model_id}' is not available. Available models: {available}. "
                "Train a model first in the Train screen."
            )
        
        model_info = self.models[model_id]
        model = model_info['model']
        label_names = model_info['label_names']
        model_type = model_info['model_type']
        
        # Convert data to numpy
        signal = np.array(signal)
        if signal.ndim == 1:
            signal = signal.reshape(1, -1)
        
        # Extract features for baseline models
        if model_type in ['logistic', 'random_forest']:
            X = self.feature_extractor.extract_dataset(signal)
        else:
            X = signal
        
        # Create predictor
        predictor = ECGPredictor(model, label_names)
        result = predictor.predict_single(X[0] if X.ndim > 1 else X)
        
        return result
    
    def explain(self, params: Dict) -> Dict:
        """Explain prediction."""
        model_id = params.get('model_id')
        predicted_class = params.get('predicted_class', params.get('prediction', ''))
        confidence = params.get('confidence', 0.5)
        
        if model_id and model_id in self.models:
            model_info = self.models[model_id]
            model = model_info['model']
            model_type = model_info['model_type']
            
            explainer = PredictionExplainer(model, model_type)
            explanation = explainer.generate_plain_language_explanation(predicted_class, confidence)
        else:
            # Generate generic explanation
            explainer = PredictionExplainer(None, 'generic')
            explanation = explainer.generate_plain_language_explanation(predicted_class, confidence)
        
        return {'explanation': explanation}
    
    def get_lessons(self, params: Dict) -> Dict:
        """Get lesson list."""
        category = params.get('category')
        lessons = self.lesson_manager.list_lessons(category)
        categories = self.lesson_manager.get_categories()
        
        return {
            'lessons': lessons,
            'categories': categories
        }
    
    def get_lesson_content(self, params: Dict) -> Dict:
        """Get lesson content."""
        lesson_id = params.get('lesson_id')
        difficulty = params.get('difficulty', 'beginner')
        
        lesson = self.lesson_manager.get_lesson(lesson_id, difficulty)
        if not lesson:
            raise ValueError(f"Lesson not found: {lesson_id}")
        
        return lesson
    
    def get_glossary(self, params: Dict) -> Dict:
        """Get glossary terms."""
        query = params.get('query')
        
        if query:
            terms = self.glossary.search(query)
        else:
            terms = self.glossary.get_all_terms()
        
        return {'terms': terms}
    
    def get_quiz_questions(self, params: Dict) -> Dict:
        """Get quiz questions."""
        category = params.get('category')
        difficulty = params.get('difficulty')
        count = params.get('count', 10)
        
        questions = self.quiz_bank.get_questions(category, difficulty, count)
        categories = self.quiz_bank.get_categories()
        
        # Format questions for TUI
        formatted_questions = []
        for q in questions:
            formatted_questions.append({
                'id': q.get('id', ''),
                'question': q.get('question', ''),
                'options': q.get('options', []),
                'category': q.get('category', category or 'General'),
                'difficulty': q.get('difficulty', 'medium')
            })
        
        return {
            'questions': formatted_questions,
            'categories': categories
        }
    
    def submit_quiz_answer(self, params: Dict) -> Dict:
        """Check quiz answer."""
        question_id = params.get('question_id')
        answer = params.get('answer')  # Can be index or answer text
        
        # Handle both index and text answers
        if isinstance(answer, int):
            answer_index = answer
        else:
            # Try to find the answer in the question options
            answer_index = 0  # Default
            question = self.quiz_bank.questions.get(question_id)
            if question:
                options = question.get('options', [])
                for i, opt in enumerate(options):
                    if opt == answer:
                        answer_index = i
                        break
        
        result = self.quiz_bank.check_answer(question_id, answer_index)
        
        # Track answer
        question = self.quiz_bank.questions.get(question_id)
        if question:
            self.quiz_tracker.record_answer(
                question_id,
                question['category'],
                result['correct']
            )
        
        return result
    
    def get_quiz_progress(self, params: Dict) -> Dict:
        """Get quiz statistics."""
        stats = self.quiz_tracker.get_statistics()
        weak_areas = self.quiz_tracker.get_weak_areas()
        
        return {
            'statistics': stats,
            'weak_areas': weak_areas
        }
