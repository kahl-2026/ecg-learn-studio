"""Model Evaluator - Comprehensive evaluation metrics"""

import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    confusion_matrix, roc_auc_score, classification_report
)
from typing import Dict, List, Optional, Tuple


class ModelEvaluator:
    """Evaluate model performance with comprehensive metrics."""
    
    def __init__(self, class_names: Optional[List[str]] = None):
        """
        Initialize evaluator.
        
        Args:
            class_names: Optional list of class names
        """
        self.class_names = class_names
    
    def evaluate(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_prob: Optional[np.ndarray] = None
    ) -> Dict:
        """
        Compute comprehensive evaluation metrics.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            y_prob: Predicted probabilities (n_samples, n_classes)
            
        Returns:
            Dictionary of metrics
        """
        metrics = {}
        
        # Basic metrics
        metrics['accuracy'] = float(accuracy_score(y_true, y_pred))
        
        # Per-class metrics
        precision, recall, f1, support = precision_recall_fscore_support(
            y_true, y_pred, average=None, zero_division=0
        )
        
        metrics['per_class'] = {}
        for i, class_name in enumerate(self.class_names or range(len(precision))):
            metrics['per_class'][str(class_name)] = {
                'precision': float(precision[i]),
                'recall': float(recall[i]),
                'f1': float(f1[i]),
                'support': int(support[i])
            }
        
        # Macro and micro averages
        precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
            y_true, y_pred, average='macro', zero_division=0
        )
        precision_micro, recall_micro, f1_micro, _ = precision_recall_fscore_support(
            y_true, y_pred, average='micro', zero_division=0
        )
        
        metrics['macro_avg'] = {
            'precision': float(precision_macro),
            'recall': float(recall_macro),
            'f1': float(f1_macro)
        }
        
        metrics['micro_avg'] = {
            'precision': float(precision_micro),
            'recall': float(recall_micro),
            'f1': float(f1_micro)
        }
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        metrics['confusion_matrix'] = cm.tolist()
        
        # ROC-AUC if probabilities provided
        if y_prob is not None:
            try:
                # Multiclass ROC-AUC (one-vs-rest)
                auc_scores = []
                n_classes = y_prob.shape[1]
                
                for i in range(n_classes):
                    y_true_binary = (y_true == i).astype(int)
                    if len(np.unique(y_true_binary)) > 1:  # Need both classes
                        auc = roc_auc_score(y_true_binary, y_prob[:, i])
                        auc_scores.append(auc)
                    else:
                        auc_scores.append(np.nan)
                
                metrics['roc_auc'] = {
                    'per_class': [float(score) if not np.isnan(score) else None 
                                  for score in auc_scores],
                    'macro': float(np.nanmean(auc_scores))
                }
            except Exception as e:
                metrics['roc_auc'] = {'error': str(e)}
        
        return metrics
    
    def get_confusion_matrix_text(self, cm: np.ndarray) -> str:
        """
        Format confusion matrix as text table.
        
        Args:
            cm: Confusion matrix
            
        Returns:
            Formatted string
        """
        lines = []
        lines.append("Confusion Matrix:")
        lines.append("-" * 50)
        
        # Header
        header = "Actual \\ Pred |"
        for i, name in enumerate(self.class_names or range(len(cm))):
            header += f" {str(name)[:8]:>8} |"
        lines.append(header)
        lines.append("-" * len(header))
        
        # Rows
        for i, row in enumerate(cm):
            actual_name = self.class_names[i] if self.class_names else str(i)
            line = f"{actual_name[:12]:>12} |"
            for val in row:
                line += f" {val:>8} |"
            lines.append(line)
        
        return "\n".join(lines)
    
    def explain_metrics(self, metrics: Dict) -> Dict[str, str]:
        """
        Generate plain-English explanations for metrics.
        
        Args:
            metrics: Metrics dictionary
            
        Returns:
            Dictionary of metric explanations
        """
        explanations = {}
        
        # Accuracy
        acc = metrics['accuracy'] * 100
        explanations['accuracy'] = (
            f"The model correctly classified {acc:.1f}% of all samples. "
            f"This means {acc:.1f} out of every 100 predictions are correct."
        )
        
        # Precision
        precision = metrics['macro_avg']['precision'] * 100
        explanations['precision'] = (
            f"When the model makes a prediction, it's correct {precision:.1f}% of the time on average. "
            f"High precision means few false alarms."
        )
        
        # Recall
        recall = metrics['macro_avg']['recall'] * 100
        explanations['recall'] = (
            f"The model successfully finds {recall:.1f}% of each arrhythmia type on average. "
            f"High recall means few missed cases."
        )
        
        # F1 Score
        f1 = metrics['macro_avg']['f1'] * 100
        explanations['f1'] = (
            f"F1 score of {f1:.1f}% balances precision and recall. "
            f"It's the harmonic mean of both metrics."
        )
        
        # ROC-AUC
        if 'roc_auc' in metrics and 'macro' in metrics['roc_auc']:
            auc = metrics['roc_auc']['macro'] * 100
            explanations['roc_auc'] = (
                f"ROC-AUC of {auc:.1f}% measures the model's ability to distinguish between classes. "
                f"50% is random guessing, 100% is perfect."
            )
        
        return explanations
    
    def generate_report(self, y_true: np.ndarray, y_pred: np.ndarray) -> str:
        """
        Generate a comprehensive text report.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            
        Returns:
            Formatted report string
        """
        target_names = self.class_names or [f"Class {i}" for i in range(len(np.unique(y_true)))]
        return classification_report(y_true, y_pred, target_names=target_names)
