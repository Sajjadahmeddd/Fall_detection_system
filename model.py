"""
LSTM-based Temporal Model for Fall Detection
Processes sequences of pose keypoints to classify FALL vs NO_FALL
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple


class FallDetectionLSTM(nn.Module):
    """
    LSTM model for temporal fall detection
    
    Input: (batch_size, sequence_length, num_features)
    Output: (batch_size, 2) - probabilities for [NO_FALL, FALL]
    """
    
    def __init__(self, 
                 input_size: int = 34,  # 17 keypoints * 2 coordinates
                 hidden_size: int = 128,
                 num_layers: int = 2,
                 dropout: float = 0.3,
                 bidirectional: bool = True):
        """
        Initialize LSTM model
        
        Args:
            input_size: Number of features per time step (num_keypoints * 2)
            hidden_size: Number of hidden units in LSTM
            num_layers: Number of stacked LSTM layers
            dropout: Dropout rate for regularization
            bidirectional: Use bidirectional LSTM
        """
        super(FallDetectionLSTM, self).__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.bidirectional = bidirectional
        self.num_directions = 2 if bidirectional else 1
        
        # LSTM layer
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=bidirectional
        )
        
        # Dropout for regularization
        self.dropout = nn.Dropout(dropout)
        
        # Fully connected layers
        fc_input_size = hidden_size * self.num_directions
        self.fc1 = nn.Linear(fc_input_size, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 2)  # Binary classification: NO_FALL (0), FALL (1)
        
        # Batch normalization
        self.bn1 = nn.BatchNorm1d(64)
        self.bn2 = nn.BatchNorm1d(32)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass
        
        Args:
            x: Input tensor of shape (batch_size, sequence_length, input_size)
            
        Returns:
            output: Logits of shape (batch_size, 2)
        """
        # LSTM layer
        # lstm_out shape: (batch_size, sequence_length, hidden_size * num_directions)
        lstm_out, (h_n, c_n) = self.lstm(x)
        
        # Take the last time step output
        # If bidirectional, concatenate forward and backward hidden states
        if self.bidirectional:
            # h_n shape: (num_layers * 2, batch_size, hidden_size)
            # Take last layer's forward and backward hidden states
            forward_hidden = h_n[-2, :, :]
            backward_hidden = h_n[-1, :, :]
            hidden = torch.cat([forward_hidden, backward_hidden], dim=1)
        else:
            # h_n shape: (num_layers, batch_size, hidden_size)
            hidden = h_n[-1, :, :]
        
        # Fully connected layers with dropout and batch norm
        x = self.dropout(hidden)
        x = F.relu(self.bn1(self.fc1(x)))
        x = self.dropout(x)
        x = F.relu(self.bn2(self.fc2(x)))
        x = self.dropout(x)
        x = self.fc3(x)
        
        return x
    
    def predict(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Predict with probabilities
        
        Args:
            x: Input tensor of shape (batch_size, sequence_length, input_size)
            
        Returns:
            predictions: Class predictions (0 or 1)
            probabilities: Softmax probabilities
        """
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            probabilities = F.softmax(logits, dim=1)
            predictions = torch.argmax(probabilities, dim=1)
        
        return predictions, probabilities


class FallDetectionGRU(nn.Module):
    """
    GRU model for temporal fall detection (alternative to LSTM)
    
    GRU is simpler and faster than LSTM while maintaining similar performance
    """
    
    def __init__(self, 
                 input_size: int = 34,
                 hidden_size: int = 128,
                 num_layers: int = 2,
                 dropout: float = 0.3,
                 bidirectional: bool = True):
        """
        Initialize GRU model
        
        Args:
            input_size: Number of features per time step
            hidden_size: Number of hidden units in GRU
            num_layers: Number of stacked GRU layers
            dropout: Dropout rate
            bidirectional: Use bidirectional GRU
        """
        super(FallDetectionGRU, self).__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.bidirectional = bidirectional
        self.num_directions = 2 if bidirectional else 1
        
        # GRU layer
        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=bidirectional
        )
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
        
        # Fully connected layers
        fc_input_size = hidden_size * self.num_directions
        self.fc1 = nn.Linear(fc_input_size, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 2)
        
        # Batch normalization
        self.bn1 = nn.BatchNorm1d(64)
        self.bn2 = nn.BatchNorm1d(32)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        # GRU layer
        gru_out, h_n = self.gru(x)
        
        # Take last hidden state
        if self.bidirectional:
            forward_hidden = h_n[-2, :, :]
            backward_hidden = h_n[-1, :, :]
            hidden = torch.cat([forward_hidden, backward_hidden], dim=1)
        else:
            hidden = h_n[-1, :, :]
        
        # Fully connected layers
        x = self.dropout(hidden)
        x = F.relu(self.bn1(self.fc1(x)))
        x = self.dropout(x)
        x = F.relu(self.bn2(self.fc2(x)))
        x = self.dropout(x)
        x = self.fc3(x)
        
        return x
    
    def predict(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Predict with probabilities"""
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            probabilities = F.softmax(logits, dim=1)
            predictions = torch.argmax(probabilities, dim=1)
        
        return predictions, probabilities


def get_model(model_type: str = 'lstm', **kwargs) -> nn.Module:
    """
    Factory function to create model
    
    Args:
        model_type: 'lstm' or 'gru'
        **kwargs: Model parameters
        
    Returns:
        model: PyTorch model
    """
    if model_type.lower() == 'lstm':
        return FallDetectionLSTM(**kwargs)
    elif model_type.lower() == 'gru':
        return FallDetectionGRU(**kwargs)
    else:
        raise ValueError(f"Unknown model type: {model_type}")


def count_parameters(model: nn.Module) -> int:
    """
    Count trainable parameters in model
    
    Args:
        model: PyTorch model
        
    Returns:
        num_params: Number of trainable parameters
    """
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == "__main__":
    """
    Test model architecture
    """
    print("Testing Fall Detection Models...")
    
    # Test parameters
    batch_size = 4
    sequence_length = 30
    num_keypoints = 17
    input_size = num_keypoints * 2  # x, y coordinates
    
    # Create dummy input
    x = torch.randn(batch_size, sequence_length, input_size)
    print(f"\nInput shape: {x.shape}")
    
    # Test LSTM model
    print("\n" + "="*50)
    print("Testing LSTM Model")
    print("="*50)
    
    lstm_model = FallDetectionLSTM(
        input_size=input_size,
        hidden_size=128,
        num_layers=2,
        dropout=0.3,
        bidirectional=True
    )
    
    print(f"Model parameters: {count_parameters(lstm_model):,}")
    print(f"\nModel architecture:")
    print(lstm_model)
    
    # Forward pass
    output = lstm_model(x)
    print(f"\nOutput shape: {output.shape}")
    print(f"Output (logits): {output[0]}")
    
    # Prediction
    predictions, probabilities = lstm_model.predict(x)
    print(f"\nPredictions: {predictions}")
    print(f"Probabilities: {probabilities[0]}")
    
    # Test GRU model
    print("\n" + "="*50)
    print("Testing GRU Model")
    print("="*50)
    
    gru_model = FallDetectionGRU(
        input_size=input_size,
        hidden_size=128,
        num_layers=2,
        dropout=0.3,
        bidirectional=True
    )
    
    print(f"Model parameters: {count_parameters(gru_model):,}")
    
    output = gru_model(x)
    print(f"Output shape: {output.shape}")
    
    predictions, probabilities = gru_model.predict(x)
    print(f"Predictions: {predictions}")
    print(f"Probabilities: {probabilities[0]}")
    
    print("\n" + "="*50)
    print("Model tests completed successfully!")
    print("="*50)
