"""
Training Script for Fall Detection Model
Includes training loop, validation, metrics, and model checkpointing
"""

import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import numpy as np
from datetime import datetime
import json
from typing import Dict, Tuple
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import seaborn as sns

from model import get_model, count_parameters
from dataset_loader import FallDetectionDataLoader, create_synthetic_dataset


class Trainer:
    """
    Trainer class for fall detection model
    """
    
    def __init__(self,
                 model: nn.Module,
                 train_loader: DataLoader,
                 val_loader: DataLoader,
                 test_loader: DataLoader,
                 device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
                 learning_rate: float = 0.001,
                 weight_decay: float = 1e-5,
                 checkpoint_dir: str = './checkpoints'):
        """
        Initialize trainer
        
        Args:
            model: PyTorch model
            train_loader: Training data loader
            val_loader: Validation data loader
            test_loader: Test data loader
            device: 'cuda' or 'cpu'
            learning_rate: Learning rate for optimizer
            weight_decay: L2 regularization weight
            checkpoint_dir: Directory to save model checkpoints
        """
        self.model = model.to(device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.test_loader = test_loader
        self.device = device
        self.checkpoint_dir = checkpoint_dir
        
        # Create checkpoint directory
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        # Loss function with class weights (to handle imbalanced data)
        self.criterion = nn.CrossEntropyLoss()
        
        # Optimizer
        self.optimizer = optim.Adam(
            model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
        
        # Learning rate scheduler
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=0.5,
            patience=5
        )
        
        # Training history
        self.history = {
            'train_loss': [],
            'train_acc': [],
            'val_loss': [],
            'val_acc': [],
            'val_precision': [],
            'val_recall': [],
            'val_f1': []
        }
        
        self.best_val_acc = 0.0
        self.best_epoch = 0
        
        print(f"Trainer initialized on device: {device}")
        print(f"Model parameters: {count_parameters(model):,}")
    
    def train_epoch(self) -> Tuple[float, float]:
        """
        Train for one epoch
        
        Returns:
            avg_loss: Average training loss
            accuracy: Training accuracy
        """
        self.model.train()
        
        total_loss = 0.0
        all_predictions = []
        all_labels = []
        
        for batch_idx, (sequences, labels) in enumerate(self.train_loader):
            # Move to device
            sequences = sequences.to(self.device)
            labels = labels.to(self.device)
            
            # Forward pass
            self.optimizer.zero_grad()
            outputs = self.model(sequences)
            loss = self.criterion(outputs, labels)
            
            # Backward pass
            loss.backward()
            
            # Gradient clipping to prevent exploding gradients
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            
            self.optimizer.step()
            
            # Track metrics
            total_loss += loss.item()
            predictions = torch.argmax(outputs, dim=1)
            all_predictions.extend(predictions.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            
            # Print progress
            if (batch_idx + 1) % 10 == 0:
                print(f"  Batch {batch_idx + 1}/{len(self.train_loader)}, Loss: {loss.item():.4f}")
        
        avg_loss = total_loss / len(self.train_loader)
        accuracy = accuracy_score(all_labels, all_predictions)
        
        return avg_loss, accuracy
    
    def validate(self, data_loader: DataLoader) -> Dict[str, float]:
        """
        Validate model
        
        Args:
            data_loader: Validation or test data loader
            
        Returns:
            metrics: Dictionary of validation metrics
        """
        self.model.eval()
        
        total_loss = 0.0
        all_predictions = []
        all_labels = []
        all_probabilities = []
        
        with torch.no_grad():
            for sequences, labels in data_loader:
                sequences = sequences.to(self.device)
                labels = labels.to(self.device)
                
                outputs = self.model(sequences)
                loss = self.criterion(outputs, labels)
                
                total_loss += loss.item()
                
                probabilities = torch.softmax(outputs, dim=1)
                predictions = torch.argmax(outputs, dim=1)
                
                all_predictions.extend(predictions.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
                all_probabilities.extend(probabilities.cpu().numpy())
        
        avg_loss = total_loss / len(data_loader)
        accuracy = accuracy_score(all_labels, all_predictions)
        precision = precision_score(all_labels, all_predictions, average='binary', zero_division=0)
        recall = recall_score(all_labels, all_predictions, average='binary', zero_division=0)
        f1 = f1_score(all_labels, all_predictions, average='binary', zero_division=0)
        
        metrics = {
            'loss': avg_loss,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'predictions': all_predictions,
            'labels': all_labels,
            'probabilities': all_probabilities
        }
        
        return metrics
    
    def train(self, num_epochs: int = 50, early_stopping_patience: int = 10):
        """
        Full training loop
        
        Args:
            num_epochs: Number of epochs to train
            early_stopping_patience: Stop if no improvement for this many epochs
        """
        print("\n" + "="*60)
        print("Starting Training")
        print("="*60)
        
        epochs_without_improvement = 0
        
        for epoch in range(num_epochs):
            print(f"\nEpoch {epoch + 1}/{num_epochs}")
            print("-" * 40)
            
            # Training
            train_loss, train_acc = self.train_epoch()
            print(f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}")
            
            # Validation
            val_metrics = self.validate(self.val_loader)
            val_loss = val_metrics['loss']
            val_acc = val_metrics['accuracy']
            val_precision = val_metrics['precision']
            val_recall = val_metrics['recall']
            val_f1 = val_metrics['f1']
            
            print(f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")
            print(f"Val Precision: {val_precision:.4f}, Val Recall: {val_recall:.4f}, Val F1: {val_f1:.4f}")
            
            # Update learning rate
            self.scheduler.step(val_loss)
            
            # Save history
            self.history['train_loss'].append(train_loss)
            self.history['train_acc'].append(train_acc)
            self.history['val_loss'].append(val_loss)
            self.history['val_acc'].append(val_acc)
            self.history['val_precision'].append(val_precision)
            self.history['val_recall'].append(val_recall)
            self.history['val_f1'].append(val_f1)
            
            # Save best model
            if val_acc > self.best_val_acc:
                self.best_val_acc = val_acc
                self.best_epoch = epoch + 1
                self.save_checkpoint('best_model.pth')
                print(f"✓ Best model saved! (Acc: {val_acc:.4f})")
                epochs_without_improvement = 0
            else:
                epochs_without_improvement += 1
            
            # Early stopping
            if epochs_without_improvement >= early_stopping_patience:
                print(f"\nEarly stopping triggered after {epoch + 1} epochs")
                break
        
        print("\n" + "="*60)
        print("Training Complete!")
        print(f"Best Validation Accuracy: {self.best_val_acc:.4f} (Epoch {self.best_epoch})")
        print("="*60)
        
        # Save final model
        self.save_checkpoint('final_model.pth')
        self.save_history()
    
    def evaluate(self) -> Dict[str, float]:
        """
        Evaluate on test set
        
        Returns:
            test_metrics: Dictionary of test metrics
        """
        print("\n" + "="*60)
        print("Evaluating on Test Set")
        print("="*60)
        
        # Load best model
        self.load_checkpoint('best_model.pth')
        
        test_metrics = self.validate(self.test_loader)
        
        print(f"\nTest Results:")
        print(f"  Accuracy:  {test_metrics['accuracy']:.4f}")
        print(f"  Precision: {test_metrics['precision']:.4f}")
        print(f"  Recall:    {test_metrics['recall']:.4f}")
        print(f"  F1 Score:  {test_metrics['f1']:.4f}")
        
        # Confusion matrix
        cm = confusion_matrix(test_metrics['labels'], test_metrics['predictions'])
        print(f"\nConfusion Matrix:")
        print(f"  True Negatives:  {cm[0, 0]}")
        print(f"  False Positives: {cm[0, 1]}")
        print(f"  False Negatives: {cm[1, 0]}")
        print(f"  True Positives:  {cm[1, 1]}")
        
        # Plot confusion matrix
        self.plot_confusion_matrix(cm)
        
        return test_metrics
    
    def save_checkpoint(self, filename: str):
        """Save model checkpoint"""
        filepath = os.path.join(self.checkpoint_dir, filename)
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'best_val_acc': self.best_val_acc,
            'best_epoch': self.best_epoch,
            'history': self.history
        }, filepath)
    
    def load_checkpoint(self, filename: str):
        """Load model checkpoint"""
        filepath = os.path.join(self.checkpoint_dir, filename)
        if os.path.exists(filepath):
            checkpoint = torch.load(filepath, map_location=self.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.best_val_acc = checkpoint.get('best_val_acc', 0.0)
            self.best_epoch = checkpoint.get('best_epoch', 0)
            print(f"Loaded checkpoint: {filename}")
        else:
            print(f"Checkpoint not found: {filepath}")
    
    def save_history(self):
        """Save training history to JSON"""
        filepath = os.path.join(self.checkpoint_dir, 'training_history.json')
        with open(filepath, 'w') as f:
            json.dump(self.history, f, indent=4)
        print(f"Training history saved to {filepath}")
        
        # Plot training curves
        self.plot_training_curves()
    
    def plot_training_curves(self):
        """Plot training and validation curves"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Loss
        axes[0, 0].plot(self.history['train_loss'], label='Train Loss')
        axes[0, 0].plot(self.history['val_loss'], label='Val Loss')
        axes[0, 0].set_xlabel('Epoch')
        axes[0, 0].set_ylabel('Loss')
        axes[0, 0].set_title('Training and Validation Loss')
        axes[0, 0].legend()
        axes[0, 0].grid(True)
        
        # Accuracy
        axes[0, 1].plot(self.history['train_acc'], label='Train Acc')
        axes[0, 1].plot(self.history['val_acc'], label='Val Acc')
        axes[0, 1].set_xlabel('Epoch')
        axes[0, 1].set_ylabel('Accuracy')
        axes[0, 1].set_title('Training and Validation Accuracy')
        axes[0, 1].legend()
        axes[0, 1].grid(True)
        
        # Precision, Recall, F1
        axes[1, 0].plot(self.history['val_precision'], label='Precision')
        axes[1, 0].plot(self.history['val_recall'], label='Recall')
        axes[1, 0].plot(self.history['val_f1'], label='F1 Score')
        axes[1, 0].set_xlabel('Epoch')
        axes[1, 0].set_ylabel('Score')
        axes[1, 0].set_title('Validation Metrics')
        axes[1, 0].legend()
        axes[1, 0].grid(True)
        
        # Hide unused subplot
        axes[1, 1].axis('off')
        
        plt.tight_layout()
        filepath = os.path.join(self.checkpoint_dir, 'training_curves.png')
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"Training curves saved to {filepath}")
        plt.close()
    
    def plot_confusion_matrix(self, cm: np.ndarray):
        """Plot confusion matrix"""
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                   xticklabels=['NO_FALL', 'FALL'],
                   yticklabels=['NO_FALL', 'FALL'])
        plt.xlabel('Predicted')
        plt.ylabel('True')
        plt.title('Confusion Matrix')
        
        filepath = os.path.join(self.checkpoint_dir, 'confusion_matrix.png')
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"Confusion matrix saved to {filepath}")
        plt.close()


def main():
    """
    Main training function
    """
    print("\n" + "="*60)
    print("FALL DETECTION MODEL TRAINING")
    print("="*60)
    
    # Configuration
    DATA_DIR = './data/synthetic_fall_dataset'
    CHECKPOINT_DIR = './checkpoints'
    SEQUENCE_LENGTH = 30
    NUM_KEYPOINTS = 17
    INPUT_SIZE = NUM_KEYPOINTS * 2
    BATCH_SIZE = 16
    NUM_EPOCHS = 50
    LEARNING_RATE = 0.001
    MODEL_TYPE = 'lstm'  # 'lstm' or 'gru'
    
    # Create synthetic dataset if it doesn't exist
    if not os.path.exists(DATA_DIR):
        print("\nCreating synthetic dataset...")
        create_synthetic_dataset(
            output_dir=DATA_DIR,
            num_fall_samples=200,
            num_no_fall_samples=200,
            sequence_length=SEQUENCE_LENGTH,
            num_keypoints=NUM_KEYPOINTS
        )
    
    # Load data
    print("\nLoading dataset...")
    data_loader = FallDetectionDataLoader(
        data_dir=DATA_DIR,
        sequence_length=SEQUENCE_LENGTH,
        test_size=0.2,
        val_size=0.1
    )
    
    train_loader, val_loader, test_loader = data_loader.create_dataloaders(
        batch_size=BATCH_SIZE,
        num_workers=0,
        augment_train=True
    )
    
    # Create model
    print(f"\nCreating {MODEL_TYPE.upper()} model...")
    model = get_model(
        model_type=MODEL_TYPE,
        input_size=INPUT_SIZE,
        hidden_size=128,
        num_layers=2,
        dropout=0.3,
        bidirectional=True
    )
    
    # Create trainer
    trainer = Trainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        test_loader=test_loader,
        learning_rate=LEARNING_RATE,
        checkpoint_dir=CHECKPOINT_DIR
    )
    
    # Train model
    trainer.train(num_epochs=NUM_EPOCHS, early_stopping_patience=10)
    
    # Evaluate on test set
    test_metrics = trainer.evaluate()
    
    print("\n" + "="*60)
    print("Training and Evaluation Complete!")
    print("="*60)


if __name__ == "__main__":
    main()
