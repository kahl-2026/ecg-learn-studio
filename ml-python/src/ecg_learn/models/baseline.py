"""Baseline Models - Logistic Regression and Random Forest"""

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
from typing import Dict, Tuple, Optional
import pickle


class BaselineModels:
    """Baseline classification models for ECG arrhythmia detection."""
    
    def __init__(self, model_type: str = 'logistic', random_state: int = 42):
        """
        Initialize baseline model.
        
        Args:
            model_type: 'logistic' or 'random_forest'
            random_state: Random seed for reproducibility
        """
        self.model_type = model_type
        self.random_state = random_state
        self.model = None
        self.is_trained = False
        
        if model_type == 'logistic':
            self.model = LogisticRegression(
                max_iter=1000,
                random_state=random_state,
                solver='lbfgs'
            )
        elif model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=random_state,
                n_jobs=-1
            )
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        class_weights: Optional[Dict] = None
    ) -> Dict:
        """
        Train the model.
        
        Args:
            X_train: Training features (n_samples, n_features)
            y_train: Training labels
            class_weights: Optional class weights for imbalance
            
        Returns:
            Training metrics
        """
        if class_weights is not None:
            if self.model_type == 'logistic':
                self.model.set_params(class_weight=class_weights)
            elif self.model_type == 'random_forest':
                self.model.set_params(class_weight=class_weights)
        
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Training accuracy
        train_score = self.model.score(X_train, y_train)
        
        return {
            'train_accuracy': float(train_score),
            'n_samples': len(X_train),
            'n_features': X_train.shape[1]
        }
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions.
        
        Args:
            X: Features (n_samples, n_features)
            
        Returns:
            Predicted class labels
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet")
        
        return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities.
        
        Args:
            X: Features (n_samples, n_features)
            
        Returns:
            Class probabilities (n_samples, n_classes)
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet")
        
        return self.model.predict_proba(X)
    
    def get_feature_importance(self, feature_names: list = None) -> Dict:
        """
        Get feature importance scores.
        
        Args:
            feature_names: Optional list of feature names
            
        Returns:
            Dictionary mapping features to importance scores
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet")
        
        if self.model_type == 'logistic':
            # Use absolute coefficient values
            importances = np.abs(self.model.coef_).mean(axis=0)
        elif self.model_type == 'random_forest':
            importances = self.model.feature_importances_
        else:
            return {}
        
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(len(importances))]
        
        # Sort by importance
        sorted_indices = np.argsort(importances)[::-1]
        
        return {
            feature_names[i]: float(importances[i])
            for i in sorted_indices
        }
    
    def hyperparameter_search(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        cv: int = 5
    ) -> Dict:
        """
        Perform hyperparameter search using GridSearchCV.
        
        Args:
            X_train: Training features
            y_train: Training labels
            cv: Number of cross-validation folds
            
        Returns:
            Best parameters and scores
        """
        if self.model_type == 'logistic':
            param_grid = {
                'C': [0.01, 0.1, 1.0, 10.0],
                'penalty': ['l2'],
                'solver': ['lbfgs']
            }
        elif self.model_type == 'random_forest':
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [5, 10, 15, None],
                'min_samples_split': [2, 5, 10]
            }
        else:
            return {}
        
        grid_search = GridSearchCV(
            self.model,
            param_grid,
            cv=cv,
            scoring='accuracy',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_train, y_train)
        
        # Update model with best parameters
        self.model = grid_search.best_estimator_
        self.is_trained = True
        
        return {
            'best_params': grid_search.best_params_,
            'best_score': float(grid_search.best_score_),
            'cv_results': {
                'mean_scores': grid_search.cv_results_['mean_test_score'].tolist(),
                'std_scores': grid_search.cv_results_['std_test_score'].tolist()
            }
        }
    
    def save(self, filepath: str):
        """Save model to file."""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        with open(filepath, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'model_type': self.model_type,
                'random_state': self.random_state
            }, f)
    
    def load(self, filepath: str):
        """Load model from file."""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        self.model = data['model']
        self.model_type = data['model_type']
        self.random_state = data['random_state']
        self.is_trained = True
