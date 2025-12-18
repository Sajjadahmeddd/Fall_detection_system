"""
Dataset Loader for Fall Detection
Loads pose sequences from NumPy arrays with sliding window support
"""

import os
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from typing import Tuple, List, Optional
import json
from sklearn.model_selection import train_test_split


class FallDetectionDataset(Dataset):
    """
    PyTorch Dataset for fall detection pose sequences
    
    Expected data format:
    - Each sample is a NumPy array of shape (sequence_length, num_keypoints * 2)
    - Labels: 0 = NO_FALL, 1 = FALL
    """
    
    def __init__(self, 
                 sequences: np.ndarray, 
                 labels: np.ndarray,
                 augment: bool = False):
        """
        Initialize dataset
        
        Args:
            sequences: numpy array of shape (num_samples, sequence_length, num_features)
            labels: numpy array of shape (num_samples,) with values 0 or 1
            augment: whether to apply data augmentation
        """
        self.sequences = torch.FloatTensor(sequences)
        self.labels = torch.LongTensor(labels)
        self.augment = augment
        
        assert len(self.sequences) == len(self.labels), \
            "Number of sequences and labels must match"
        
    def __len__(self) -> int:
        return len(self.sequences)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Get a single sample
        
        Args:
            idx: index
            
        Returns:
            sequence: (sequence_length, num_features)
            label: scalar (0 or 1)
        """
        sequence = self.sequences[idx]
        label = self.labels[idx]
        
        # Apply augmentation if enabled
        if self.augment:
            sequence = self._augment_sequence(sequence)
        
        return sequence, label
    
    def _augment_sequence(self, sequence: torch.Tensor) -> torch.Tensor:
        """
        Apply data augmentation to a sequence
        
        Augmentation techniques:
        - Random temporal scaling (speed up/slow down)
        - Random noise injection
        - Random horizontal flip
        
        Args:
            sequence: (sequence_length, num_features)
            
        Returns:
            augmented_sequence: same shape
        """
        # Random noise (5% chance)
        if np.random.rand() < 0.05:
            noise = torch.randn_like(sequence) * 0.02
            sequence = sequence + noise
        
        # Random horizontal flip (swap left/right keypoints)
        # This requires knowledge of keypoint structure
        # For simplicity, we'll skip this for now
        
        return sequence


class FallDetectionDataLoader:
    """
    Data loader manager for fall detection
    Handles loading from directory structure and creating train/val/test splits
    """
    
    def __init__(self, 
                 data_dir: str,
                 sequence_length: int = 30,
                 test_size: float = 0.2,
                 val_size: float = 0.1,
                 random_state: int = 42):
        """
        Initialize data loader
        
        Args:
            data_dir: Root directory containing data
                     Expected structure:
                     data_dir/
                         fall/
                             sequence_001.npy
                             sequence_002.npy
                             ...
                         no_fall/
                             sequence_001.npy
                             sequence_002.npy
                             ...
            sequence_length: Expected sequence length
            test_size: Proportion of data for testing
            val_size: Proportion of training data for validation
            random_state: Random seed for reproducibility
        """
        self.data_dir = data_dir
        self.sequence_length = sequence_length
        self.test_size = test_size
        self.val_size = val_size
        self.random_state = random_state
        
    def load_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load all sequences and labels from directory
        
        Returns:
            sequences: (num_samples, sequence_length, num_features)
            labels: (num_samples,)
        """
        fall_dir = os.path.join(self.data_dir, 'fall')
        no_fall_dir = os.path.join(self.data_dir, 'no_fall')
        
        sequences = []
        labels = []
        
        # Load fall sequences (label = 1)
        if os.path.exists(fall_dir):
            print(f"Loading fall sequences from {fall_dir}...")
            for filename in os.listdir(fall_dir):
                if filename.endswith('.npy'):
                    filepath = os.path.join(fall_dir, filename)
                    seq = np.load(filepath)
                    
                    # Validate shape
                    if seq.shape[0] == self.sequence_length:
                        sequences.append(seq)
                        labels.append(1)
                    else:
                        print(f"Warning: {filename} has incorrect shape {seq.shape}, skipping")
            
            print(f"Loaded {sum(labels)} fall sequences")
        else:
            print(f"Warning: Fall directory not found: {fall_dir}")
        
        # Load no_fall sequences (label = 0)
        if os.path.exists(no_fall_dir):
            print(f"Loading no_fall sequences from {no_fall_dir}...")
            initial_count = len(labels)
            for filename in os.listdir(no_fall_dir):
                if filename.endswith('.npy'):
                    filepath = os.path.join(no_fall_dir, filename)
                    seq = np.load(filepath)
                    
                    if seq.shape[0] == self.sequence_length:
                        sequences.append(seq)
                        labels.append(0)
                    else:
                        print(f"Warning: {filename} has incorrect shape {seq.shape}, skipping")
            
            print(f"Loaded {len(labels) - initial_count} no_fall sequences")
        else:
            print(f"Warning: No_fall directory not found: {no_fall_dir}")
        
        if len(sequences) == 0:
            raise ValueError("No valid sequences found!")
        
        sequences = np.array(sequences, dtype=np.float32)
        labels = np.array(labels, dtype=np.int64)
        
        print(f"\nTotal sequences loaded: {len(sequences)}")
        print(f"Sequence shape: {sequences.shape}")
        print(f"Fall samples: {np.sum(labels == 1)}")
        print(f"No-fall samples: {np.sum(labels == 0)}")
        
        return sequences, labels
    
    def create_dataloaders(self, 
                          batch_size: int = 32,
                          num_workers: int = 0,
                          augment_train: bool = True) -> Tuple[DataLoader, DataLoader, DataLoader]:
        """
        Create train, validation, and test data loaders
        
        Args:
            batch_size: Batch size for training
            num_workers: Number of worker processes for data loading
            augment_train: Apply augmentation to training data
            
        Returns:
            train_loader, val_loader, test_loader
        """
        # Load all data
        sequences, labels = self.load_data()
        
        # Split into train+val and test
        X_trainval, X_test, y_trainval, y_test = train_test_split(
            sequences, labels,
            test_size=self.test_size,
            random_state=self.random_state,
            stratify=labels
        )
        
        # Split train+val into train and val
        X_train, X_val, y_train, y_val = train_test_split(
            X_trainval, y_trainval,
            test_size=self.val_size,
            random_state=self.random_state,
            stratify=y_trainval
        )
        
        print(f"\nDataset splits:")
        print(f"  Train: {len(X_train)} samples")
        print(f"  Val:   {len(X_val)} samples")
        print(f"  Test:  {len(X_test)} samples")
        
        # Create datasets
        train_dataset = FallDetectionDataset(X_train, y_train, augment=augment_train)
        val_dataset = FallDetectionDataset(X_val, y_val, augment=False)
        test_dataset = FallDetectionDataset(X_test, y_test, augment=False)
        
        # Create data loaders
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
            pin_memory=True
        )
        
        val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=True
        )
        
        test_loader = DataLoader(
            test_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=True
        )
        
        return train_loader, val_loader, test_loader


def create_synthetic_dataset(output_dir: str, 
                            num_fall_samples: int = 100,
                            num_no_fall_samples: int = 100,
                            sequence_length: int = 30,
                            num_keypoints: int = 17):
    """
    Create a synthetic dataset for testing purposes
    
    This generates random pose sequences with simulated fall patterns
    
    Args:
        output_dir: Directory to save synthetic data
        num_fall_samples: Number of fall sequences to generate
        num_no_fall_samples: Number of no-fall sequences to generate
        sequence_length: Length of each sequence
        num_keypoints: Number of keypoints (default 17 for MediaPipe)
    """
    os.makedirs(output_dir, exist_ok=True)
    fall_dir = os.path.join(output_dir, 'fall')
    no_fall_dir = os.path.join(output_dir, 'no_fall')
    os.makedirs(fall_dir, exist_ok=True)
    os.makedirs(no_fall_dir, exist_ok=True)
    
    num_features = num_keypoints * 2
    
    print(f"Creating synthetic dataset in {output_dir}...")
    
    # Generate fall sequences
    print(f"Generating {num_fall_samples} fall sequences...")
    for i in range(num_fall_samples):
        # Simulate a fall: gradual decrease in vertical positions
        sequence = np.random.randn(sequence_length, num_features).astype(np.float32) * 0.1
        
        # Simulate falling motion (y-coordinates decrease)
        for t in range(sequence_length):
            progress = t / sequence_length
            # Decrease vertical positions (odd indices are y-coordinates)
            sequence[t, 1::2] -= progress * 0.5
        
        filepath = os.path.join(fall_dir, f'fall_sequence_{i:04d}.npy')
        np.save(filepath, sequence)
    
    # Generate no-fall sequences
    print(f"Generating {num_no_fall_samples} no-fall sequences...")
    for i in range(num_no_fall_samples):
        # Random walking motion (stable)
        sequence = np.random.randn(sequence_length, num_features).astype(np.float32) * 0.05
        
        # Add slight oscillations (normal movement)
        for t in range(sequence_length):
            phase = 2 * np.pi * t / sequence_length
            sequence[t, :] += np.sin(phase) * 0.02
        
        filepath = os.path.join(no_fall_dir, f'no_fall_sequence_{i:04d}.npy')
        np.save(filepath, sequence)
    
    print(f"Synthetic dataset created successfully!")
    print(f"  Fall samples: {num_fall_samples}")
    print(f"  No-fall samples: {num_no_fall_samples}")
    print(f"  Sequence length: {sequence_length}")
    print(f"  Features per frame: {num_features}")


if __name__ == "__main__":
    """
    Test dataset loader with synthetic data
    """
    print("Testing Dataset Loader...")
    
    # Create synthetic dataset
    data_dir = './data/synthetic_fall_dataset'
    create_synthetic_dataset(
        output_dir=data_dir,
        num_fall_samples=50,
        num_no_fall_samples=50,
        sequence_length=30
    )
    
    # Test data loader
    print("\n" + "="*50)
    print("Testing Data Loader")
    print("="*50)
    
    loader = FallDetectionDataLoader(
        data_dir=data_dir,
        sequence_length=30,
        test_size=0.2,
        val_size=0.1
    )
    
    train_loader, val_loader, test_loader = loader.create_dataloaders(
        batch_size=8,
        num_workers=0,
        augment_train=True
    )
    
    # Test iteration
    print("\nTesting batch iteration...")
    for batch_idx, (sequences, labels) in enumerate(train_loader):
        print(f"Batch {batch_idx + 1}:")
        print(f"  Sequences shape: {sequences.shape}")
        print(f"  Labels shape: {labels.shape}")
        print(f"  Labels: {labels.tolist()}")
        
        if batch_idx >= 2:  # Show first 3 batches
            break
    
    print("\n" + "="*50)
    print("Dataset loader test completed!")
    print("="*50)
