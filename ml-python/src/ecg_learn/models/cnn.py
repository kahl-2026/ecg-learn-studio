"""1D CNN for ECG Classification"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, Tuple


class ECG_CNN(nn.Module):
    """1D Convolutional Neural Network for ECG arrhythmia classification."""
    
    def __init__(
        self,
        input_length: int = 3600,
        n_classes: int = 5,
        n_channels: int = 32
    ):
        """
        Initialize 1D CNN.
        
        Args:
            input_length: Length of input signal
            n_classes: Number of output classes
            n_channels: Base number of convolutional channels
        """
        super(ECG_CNN, self).__init__()
        
        self.input_length = input_length
        self.n_classes = n_classes
        
        # Convolutional blocks
        self.conv1 = nn.Conv1d(1, n_channels, kernel_size=5, padding=2)
        self.bn1 = nn.BatchNorm1d(n_channels)
        self.pool1 = nn.MaxPool1d(2)
        self.dropout1 = nn.Dropout(0.2)
        
        self.conv2 = nn.Conv1d(n_channels, n_channels*2, kernel_size=5, padding=2)
        self.bn2 = nn.BatchNorm1d(n_channels*2)
        self.pool2 = nn.MaxPool1d(2)
        self.dropout2 = nn.Dropout(0.2)
        
        self.conv3 = nn.Conv1d(n_channels*2, n_channels*4, kernel_size=5, padding=2)
        self.bn3 = nn.BatchNorm1d(n_channels*4)
        self.pool3 = nn.MaxPool1d(2)
        self.dropout3 = nn.Dropout(0.3)
        
        self.conv4 = nn.Conv1d(n_channels*4, n_channels*8, kernel_size=5, padding=2)
        self.bn4 = nn.BatchNorm1d(n_channels*8)
        self.pool4 = nn.MaxPool1d(2)
        self.dropout4 = nn.Dropout(0.3)
        
        # Calculate flattened size
        self.flat_size = (input_length // 16) * n_channels * 8
        
        # Fully connected layers
        self.fc1 = nn.Linear(self.flat_size, 128)
        self.dropout_fc1 = nn.Dropout(0.5)
        self.fc2 = nn.Linear(128, n_classes)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Input tensor (batch_size, 1, input_length)
            
        Returns:
            Output logits (batch_size, n_classes)
        """
        # Conv block 1
        x = self.conv1(x)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.pool1(x)
        x = self.dropout1(x)
        
        # Conv block 2
        x = self.conv2(x)
        x = self.bn2(x)
        x = F.relu(x)
        x = self.pool2(x)
        x = self.dropout2(x)
        
        # Conv block 3
        x = self.conv3(x)
        x = self.bn3(x)
        x = F.relu(x)
        x = self.pool3(x)
        x = self.dropout3(x)
        
        # Conv block 4
        x = self.conv4(x)
        x = self.bn4(x)
        x = F.relu(x)
        x = self.pool4(x)
        x = self.dropout4(x)
        
        # Flatten
        x = x.view(x.size(0), -1)
        
        # Fully connected
        x = self.fc1(x)
        x = F.relu(x)
        x = self.dropout_fc1(x)
        x = self.fc2(x)
        
        return x
    
    def predict(self, x: torch.Tensor) -> torch.Tensor:
        """
        Make predictions with softmax.
        
        Args:
            x: Input tensor
            
        Returns:
            Class predictions
        """
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            predictions = torch.argmax(logits, dim=1)
        return predictions
    
    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        """
        Get class probabilities.
        
        Args:
            x: Input tensor
            
        Returns:
            Class probabilities
        """
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            probabilities = F.softmax(logits, dim=1)
        return probabilities
    
    def get_num_parameters(self) -> int:
        """Get total number of trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


class ECGCNNWrapper:
    """Wrapper for ECG_CNN to match sklearn-like interface."""
    
    def __init__(
        self,
        input_length: int = 3600,
        n_classes: int = 5,
        device: str = None
    ):
        """
        Initialize CNN wrapper.
        
        Args:
            input_length: Input signal length
            n_classes: Number of classes
            device: 'cuda', 'cpu', or None (auto-detect)
        """
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        self.model = ECG_CNN(input_length, n_classes).to(self.device)
        self.n_classes = n_classes
        self.is_trained = False
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions.
        
        Args:
            X: Input signals (n_samples, signal_length)
            
        Returns:
            Predicted labels
        """
        X_tensor = torch.FloatTensor(X).unsqueeze(1).to(self.device)
        predictions = self.model.predict(X_tensor)
        return predictions.cpu().numpy()
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Get class probabilities.
        
        Args:
            X: Input signals
            
        Returns:
            Class probabilities (n_samples, n_classes)
        """
        X_tensor = torch.FloatTensor(X).unsqueeze(1).to(self.device)
        probabilities = self.model.predict_proba(X_tensor)
        return probabilities.cpu().numpy()
    
    def save(self, filepath: str):
        """Save model weights."""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'n_classes': self.n_classes,
            'input_length': self.model.input_length
        }, filepath)
    
    def load(self, filepath: str):
        """Load model weights."""
        checkpoint = torch.load(filepath, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()
        self.is_trained = True
