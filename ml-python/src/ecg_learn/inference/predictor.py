"""ECG Predictor - Run inference with trained models"""

import numpy as np
from typing import Dict, List, Optional, Tuple


class ECGPredictor:
    """Make predictions on ECG data with confidence estimation."""
    
    def __init__(
        self,
        model,
        class_names: List[str],
        confidence_threshold: float = 0.7
    ):
        """
        Initialize predictor.
        
        Args:
            model: Trained model instance
            class_names: List of class names
            confidence_threshold: Minimum confidence for certain prediction
        """
        self.model = model
        self.class_names = class_names
        self.confidence_threshold = confidence_threshold
    
    def predict_single(self, signal: np.ndarray) -> Dict:
        """
        Predict on a single ECG signal.
        
        Args:
            signal: ECG signal array
            
        Returns:
            Prediction results dictionary
        """
        # Ensure correct shape
        if signal.ndim == 1:
            signal = signal.reshape(1, -1)
        
        # Get prediction and probabilities
        prediction = self.model.predict(signal)[0]
        probabilities = self.model.predict_proba(signal)[0]
        
        # Get top predictions
        top_indices = np.argsort(probabilities)[::-1]
        
        result = {
            'prediction': self.class_names[prediction],
            'predicted_class': self.class_names[prediction],
            'prediction_idx': int(prediction),
            'confidence': float(probabilities[prediction]),
            'probabilities': {
                self.class_names[i]: float(probabilities[i])
                for i in range(len(self.class_names))
            },
            'top_predictions': [
                {
                    'class': self.class_names[idx],
                    'label': self.class_names[idx],
                    'probability': float(probabilities[idx])
                }
                for idx in top_indices[:3]
            ],
            'uncertainty_warning': probabilities[prediction] < self.confidence_threshold,
            'is_uncertain': probabilities[prediction] < self.confidence_threshold,
        }
        
        # Add uncertainty explanation
        if result['uncertainty_warning']:
            result['uncertainty_message'] = (
                f"The model's confidence ({probabilities[prediction]:.1%}) is below the "
                f"threshold ({self.confidence_threshold:.1%}). Prediction may be uncertain."
            )
        
        return result
    
    def predict_batch(self, signals: np.ndarray) -> List[Dict]:
        """
        Predict on multiple signals.
        
        Args:
            signals: Array of signals (n_samples, signal_length)
            
        Returns:
            List of prediction dictionaries
        """
        return [self.predict_single(signal) for signal in signals]
    
    def get_prediction_summary(self, predictions: List[Dict]) -> Dict:
        """
        Summarize batch predictions.
        
        Args:
            predictions: List of prediction dictionaries
            
        Returns:
            Summary statistics
        """
        n_predictions = len(predictions)
        n_uncertain = sum(1 for p in predictions if p['uncertainty_warning'])
        
        # Count predictions per class
        class_counts = {name: 0 for name in self.class_names}
        for pred in predictions:
            class_counts[pred['prediction']] += 1
        
        # Average confidence
        avg_confidence = np.mean([p['confidence'] for p in predictions])
        
        return {
            'total_predictions': n_predictions,
            'uncertain_count': n_uncertain,
            'uncertain_percentage': (n_uncertain / n_predictions * 100) if n_predictions > 0 else 0,
            'class_distribution': class_counts,
            'average_confidence': float(avg_confidence)
        }
