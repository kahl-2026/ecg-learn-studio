"""Model Trainer - Training loop for all model types"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from typing import Dict, Callable, Optional, List
from ..models.baseline import BaselineModels
from ..models.cnn import ECGCNNWrapper


class ModelTrainer:
    """Unified trainer for all model types."""
    
    def __init__(
        self,
        model,
        model_type: str,
        random_state: int = 42
    ):
        """
        Initialize trainer.
        
        Args:
            model: Model instance
            model_type: 'logistic', 'random_forest', or 'cnn'
            random_state: Random seed
        """
        self.model = model
        self.model_type = model_type
        self.random_state = random_state
        self.history = {'train_loss': [], 'val_loss': [], 'train_acc': [], 'val_acc': []}
    
    def train_baseline(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        class_weights: Optional[Dict] = None
    ) -> Dict:
        """
        Train baseline model (Logistic Regression or Random Forest).
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features
            y_val: Validation labels
            class_weights: Optional class weights
            
        Returns:
            Training history
        """
        # Train model
        train_metrics = self.model.train(X_train, y_train, class_weights)
        
        # Compute validation metrics if provided
        if X_val is not None and y_val is not None:
            val_predictions = self.model.predict(X_val)
            val_acc = np.mean(val_predictions == y_val)
            train_metrics['val_accuracy'] = float(val_acc)
        
        return train_metrics
    
    def train_cnn(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        epochs: int = 50,
        batch_size: int = 32,
        learning_rate: float = 0.001,
        class_weights: Optional[torch.Tensor] = None,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Train CNN model.
        
        Args:
            X_train: Training signals
            y_train: Training labels
            X_val: Validation signals
            y_val: Validation labels
            epochs: Number of training epochs
            batch_size: Batch size
            learning_rate: Learning rate
            class_weights: Optional class weights tensor
            progress_callback: Callback for progress updates
            
        Returns:
            Training history
        """
        device = self.model.device
        
        # Prepare data loaders
        X_train_tensor = torch.FloatTensor(X_train).unsqueeze(1)
        y_train_tensor = torch.LongTensor(y_train)
        train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        
        if X_val is not None and y_val is not None:
            X_val_tensor = torch.FloatTensor(X_val).unsqueeze(1)
            y_val_tensor = torch.LongTensor(y_val)
            val_dataset = TensorDataset(X_val_tensor, y_val_tensor)
            val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
        else:
            val_loader = None
        
        # Loss and optimizer
        if class_weights is not None:
            criterion = nn.CrossEntropyLoss(weight=class_weights.to(device))
        else:
            criterion = nn.CrossEntropyLoss()
        
        optimizer = optim.Adam(self.model.model.parameters(), lr=learning_rate)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=5, factor=0.5)
        
        # Training loop
        best_val_loss = float('inf')
        
        for epoch in range(epochs):
            # Training phase
            self.model.model.train()
            train_loss = 0.0
            train_correct = 0
            train_total = 0
            
            for batch_X, batch_y in train_loader:
                batch_X = batch_X.to(device)
                batch_y = batch_y.to(device)
                
                optimizer.zero_grad()
                outputs = self.model.model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                train_total += batch_y.size(0)
                train_correct += (predicted == batch_y).sum().item()
            
            avg_train_loss = train_loss / len(train_loader)
            train_accuracy = train_correct / train_total
            
            self.history['train_loss'].append(avg_train_loss)
            self.history['train_acc'].append(train_accuracy)
            
            # Validation phase
            if val_loader is not None:
                self.model.model.eval()
                val_loss = 0.0
                val_correct = 0
                val_total = 0
                
                with torch.no_grad():
                    for batch_X, batch_y in val_loader:
                        batch_X = batch_X.to(device)
                        batch_y = batch_y.to(device)
                        
                        outputs = self.model.model(batch_X)
                        loss = criterion(outputs, batch_y)
                        
                        val_loss += loss.item()
                        _, predicted = torch.max(outputs.data, 1)
                        val_total += batch_y.size(0)
                        val_correct += (predicted == batch_y).sum().item()
                
                avg_val_loss = val_loss / len(val_loader)
                val_accuracy = val_correct / val_total
                
                self.history['val_loss'].append(avg_val_loss)
                self.history['val_acc'].append(val_accuracy)
                
                # Learning rate scheduling
                scheduler.step(avg_val_loss)
                
                # Track best model
                if avg_val_loss < best_val_loss:
                    best_val_loss = avg_val_loss
            else:
                avg_val_loss = None
                val_accuracy = None
            
            # Progress callback
            if progress_callback is not None:
                progress_callback({
                    'epoch': epoch + 1,
                    'total_epochs': epochs,
                    'train_loss': avg_train_loss,
                    'train_acc': train_accuracy,
                    'val_loss': avg_val_loss,
                    'val_acc': val_accuracy
                })
        
        self.model.is_trained = True
        
        return {
            'history': self.history,
            'final_train_accuracy': train_accuracy,
            'final_val_accuracy': val_accuracy if val_accuracy is not None else None,
            'best_val_loss': best_val_loss if val_loader is not None else None
        }
    
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        validation_split: float = 0.2,
        **kwargs
    ) -> Dict:
        """
        Train model with automatic train/val split.
        
        Args:
            X_train: Training data
            y_train: Training labels
            validation_split: Fraction for validation
            **kwargs: Model-specific training arguments
            
        Returns:
            Training results
        """
        # Split data
        if validation_split > 0:
            X_train_split, X_val, y_train_split, y_val = train_test_split(
                X_train, y_train,
                test_size=validation_split,
                random_state=self.random_state,
                stratify=y_train
            )
        else:
            X_train_split, y_train_split = X_train, y_train
            X_val, y_val = None, None
        
        # Train based on model type
        if self.model_type in ['logistic', 'random_forest']:
            return self.train_baseline(X_train_split, y_train_split, X_val, y_val, **kwargs)
        elif self.model_type == 'cnn':
            return self.train_cnn(X_train_split, y_train_split, X_val, y_val, **kwargs)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
