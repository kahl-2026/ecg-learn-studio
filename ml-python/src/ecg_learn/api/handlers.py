"""Request Handlers - Process API method calls"""

import numpy as np
from typing import Dict, Any
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
            'train_model': self.train_model,
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
                n_samples_per_class=count // 5
            )
            
            dataset_id = f"synthetic_{len(self.datasets)}"
            self.datasets[dataset_id] = {
                'signals': signals,
                'labels': labels,
                'label_names': label_names,
                'type': 'synthetic'
            }
            
            # Get class distribution
            unique, counts = np.unique(labels, return_counts=True)
            class_dist = {label_names[i]: int(counts[i]) for i, _ in enumerate(unique)}
            
            return {
                'dataset_id': dataset_id,
                'sample_count': len(signals),
                'class_distribution': class_dist,
                'sampling_rate': 360,
                'signal_length': signals.shape[1]
            }
        
        else:
            raise ValueError(f"Unsupported dataset type: {dataset_type}")
    
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
    
    def train_model(self, params: Dict) -> Dict:
        """Train a model."""
        model_type = params.get('model_type', 'logistic')
        dataset_id = params.get('dataset_id')
        
        if dataset_id not in self.datasets:
            raise ValueError(f"Dataset not found: {dataset_id}")
        
        dataset = self.datasets[dataset_id]
        X = dataset['signals']
        y = dataset['labels']
        label_names = dataset['label_names']
        
        # Create model
        model = ModelRegistry.create_model(model_type)
        
        # For baseline models, extract features
        if model_type in ['logistic', 'random_forest']:
            extractor = ECGFeatureExtractor()
            X_features = extractor.extract_dataset(X)
        else:
            X_features = X
        
        # Train
        trainer = ModelTrainer(model, model_type)
        results = trainer.train(X_features, y, validation_split=0.2)
        
        # Evaluate
        if model_type in ['logistic', 'random_forest']:
            y_pred = model.predict(X_features)
            y_prob = model.predict_proba(X_features)
        else:
            y_pred = model.predict(X)
            y_prob = model.predict_proba(X)
        
        evaluator = ModelEvaluator(label_names)
        metrics = evaluator.evaluate(y, y_pred, y_prob)
        
        # Store model
        model_id = f"{model_type}_{len(self.models)}"
        self.models[model_id] = {
            'model': model,
            'model_type': model_type,
            'label_names': label_names,
            'metrics': metrics
        }
        
        return {
            'model_id': model_id,
            'final_metrics': metrics,
            'training_history': results.get('history', {})
        }
    
    def predict(self, params: Dict) -> Dict:
        """Make predictions."""
        model_id = params.get('model_id')
        data = params.get('data')  # Signal as list
        
        if model_id not in self.models:
            raise ValueError(f"Model not found: {model_id}")
        
        model_info = self.models[model_id]
        model = model_info['model']
        label_names = model_info['label_names']
        
        # Convert data to numpy
        signal = np.array(data)
        
        # Create predictor
        predictor = ECGPredictor(model, label_names)
        result = predictor.predict_single(signal)
        
        return result
    
    def explain(self, params: Dict) -> Dict:
        """Explain prediction."""
        model_id = params.get('model_id')
        prediction = params.get('prediction')
        confidence = params.get('confidence', 0.5)
        
        if model_id not in self.models:
            raise ValueError(f"Model not found: {model_id}")
        
        model_info = self.models[model_id]
        model = model_info['model']
        model_type = model_info['model_type']
        
        explainer = PredictionExplainer(model, model_type)
        explanation = explainer.generate_plain_language_explanation(prediction, confidence)
        
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
        
        return {
            'questions': questions,
            'categories': categories
        }
    
    def submit_quiz_answer(self, params: Dict) -> Dict:
        """Check quiz answer."""
        question_id = params.get('question_id')
        answer_index = params.get('answer_index')
        
        result = self.quiz_bank.check_answer(question_id, answer_index)
        
        # Track if answer provided
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
