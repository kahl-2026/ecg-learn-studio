"""Prediction Explainer - Explain model decisions"""

import numpy as np
from typing import Dict, Optional, List


class PredictionExplainer:
    """Explain predictions for interpretability."""
    
    def __init__(self, model, model_type: str):
        """
        Initialize explainer.
        
        Args:
            model: Trained model
            model_type: Type of model
        """
        self.model = model
        self.model_type = model_type
    
    def explain_prediction(
        self,
        signal: np.ndarray,
        features: Optional[np.ndarray] = None,
        feature_names: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate explanation for a prediction.
        
        Args:
            signal: ECG signal
            features: Extracted features (for baseline models)
            feature_names: Names of features
            
        Returns:
            Explanation dictionary
        """
        explanation = {
            'method': self.model_type,
            'features': []
        }
        
        if self.model_type in ['logistic', 'random_forest'] and features is not None:
            # Feature importance explanation
            importance = self.model.get_feature_importance(feature_names)
            
            # Get top features
            top_features = list(importance.items())[:5]
            
            explanation['features'] = [
                {
                    'name': name,
                    'importance': float(score),
                    'value': float(features[0, i]) if i < len(features[0]) else None
                }
                for i, (name, score) in enumerate(top_features)
            ]
            
            explanation['interpretation'] = (
                f"The model's decision was primarily influenced by: "
                + ", ".join([f"{name} ({score:.3f})" for name, score in top_features[:3]])
            )
        
        elif self.model_type == 'cnn':
            # For CNN, we can provide general explanation
            explanation['interpretation'] = (
                "The neural network analyzed the ECG waveform patterns, "
                "focusing on QRS complex morphology, rhythm regularity, "
                "and characteristic patterns of the detected arrhythmia."
            )
            
            # Could add gradient-based saliency maps in future
            explanation['note'] = "Deep learning models focus on learned patterns in the raw signal."
        
        return explanation
    
    def generate_plain_language_explanation(
        self,
        prediction: str,
        confidence: float
    ) -> str:
        """
        Generate plain-language explanation of prediction.
        
        Args:
            prediction: Predicted class name
            confidence: Prediction confidence
            
        Returns:
            Plain English explanation
        """
        explanations = {
            'normal': (
                "The ECG shows normal sinus rhythm with regular P waves, QRS complexes, "
                "and T waves. Heart rate and intervals are within normal limits."
            ),
            'afib': (
                "Atrial fibrillation detected: irregular RR intervals and absence of distinct P waves. "
                "The atria are quivering rather than contracting normally."
            ),
            'bradycardia': (
                "Bradycardia detected: heart rate is slower than normal (<60 bpm). "
                "This may be normal for athletes or indicate conduction issues."
            ),
            'tachycardia': (
                "Tachycardia detected: heart rate is faster than normal (>100 bpm). "
                "Could be due to exercise, stress, or cardiac conditions."
            ),
            'pvc': (
                "Premature Ventricular Contractions detected: extra heartbeats originating "
                "from the ventricles, appearing as wide, bizarre QRS complexes."
            )
        }
        
        explanation = explanations.get(prediction.lower(), "No explanation available.")
        confidence_text = f"Model confidence: {confidence:.1%}. "
        
        if confidence >= 0.9:
            confidence_text += "Very confident prediction."
        elif confidence >= 0.7:
            confidence_text += "Moderately confident prediction."
        else:
            confidence_text += "Low confidence - use caution."
        
        return explanation + " " + confidence_text
