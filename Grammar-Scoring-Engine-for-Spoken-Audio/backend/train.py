"""
Training script for Grammar Scoring Model
"""
import argparse
import pandas as pd
import numpy as np
import torch
from torch.utils.data import DataLoader
from torch.optim import AdamW
from transformers import AutoTokenizer, get_linear_schedule_with_warmup
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from tqdm import tqdm
import json

from config import (
    DATASET_DIR, AUDIO_TRAIN_DIR, MODELS_DIR,
    MODEL_NAME, NUM_LABELS, MAX_LENGTH, BATCH_SIZE,
    LEARNING_RATE, NUM_EPOCHS, WARMUP_RATIO,
    SCORE_TO_LABEL, LABEL_TO_SCORE
)
from model import GrammarDataset, GrammarScoringModel, GrammarScorer
from transcription import TranscriptionService


def load_training_data(csv_path: Path, audio_dir: Path,
                       transcription_service: TranscriptionService) -> pd.DataFrame:
    """Load and prepare training data with transcriptions"""
    df = pd.read_csv(csv_path)
    
    # Clean and convert labels
    df['label'] = pd.to_numeric(df['label'], errors='coerce')
    df = df.dropna(subset=['label'])
    
    # Ensure labels are valid scores (0-5)
    df = df[(df['label'] >= 0) & (df['label'] <= 5)]
    
    transcripts = []
    valid_indices = []
    
    print("Transcribing audio files...")
    for idx, row in tqdm(df.iterrows(), total=len(df)):
        audio_path = audio_dir / row['filename']
        
        if not audio_path.exists():
            print(f"Warning: Audio file not found: {audio_path}")
            continue
        
        try:
            result = transcription_service.transcribe(audio_path)
            transcripts.append(result['text'])
            valid_indices.append(idx)
        except Exception as e:
            print(f"Error transcribing {row['filename']}: {e}")
    
    df = df.iloc[valid_indices].copy()
    df['transcript'] = transcripts
    
    return df


def train_model(train_df: pd.DataFrame, val_df: pd.DataFrame,
                epochs: int = NUM_EPOCHS, batch_size: int = BATCH_SIZE,
                learning_rate: float = LEARNING_RATE,
                save_path: Path = MODELS_DIR / "deberta_classifier.pt",
                resume: bool = False):
    """Train the grammar scoring model"""
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # Initialize tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = GrammarScoringModel()
    
    # Ensure model uses float32 to avoid dtype mismatch
    model = model.float()
    model = model.to(device)

    # Resume from checkpoint if requested
    if resume and save_path.exists():
        print(f"Resuming training from {save_path}")
        try:
            model.load_state_dict(torch.load(save_path))
            print("Successfully loaded saved model weights")
        except Exception as e:
            print(f"Error loading model weights: {e}")
            print("Starting training from scratch")
    
    # Create datasets
    train_dataset = GrammarDataset(
        train_df['transcript'].tolist(),
        train_df['label'].tolist(),
        tokenizer
    )
    val_dataset = GrammarDataset(
        val_df['transcript'].tolist(),
        val_df['label'].tolist(),
        tokenizer
    )
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    # Optimizer and scheduler
    optimizer = AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)
    
    total_steps = len(train_loader) * epochs
    warmup_steps = int(total_steps * WARMUP_RATIO)
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps
    )
    
    # Training history
    history = {
        'train_loss': [], 'val_loss': [],
        'train_acc': [], 'val_acc': [],
        'val_rmse': []
    }
    
    best_val_loss = float('inf')
    
    print(f"\nStarting training for {epochs} epochs...")
    print(f"Train samples: {len(train_dataset)}, Val samples: {len(val_dataset)}")
    
    for epoch in range(epochs):
        # Training
        model.train()
        train_loss = 0
        train_preds = []
        train_labels = []
        
        for batch in tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}"):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            
            optimizer.zero_grad()
            outputs = model(input_ids, attention_mask, labels)
            loss = outputs['loss']
            
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            
            train_loss += loss.item()
            preds = torch.argmax(outputs['logits'], dim=-1)
            train_preds.extend(preds.cpu().numpy())
            train_labels.extend(labels.cpu().numpy())
        
        train_loss /= len(train_loader)
        train_acc = accuracy_score(train_labels, train_preds)
        
        # Validation
        model.eval()
        val_loss = 0
        val_preds = []
        val_labels = []
        val_scores_pred = []
        val_scores_true = []
        
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['labels'].to(device)
                scores_true = batch['score']
                
                outputs = model(input_ids, attention_mask, labels)
                val_loss += outputs['loss'].item()
                
                preds = torch.argmax(outputs['logits'], dim=-1)
                val_preds.extend(preds.cpu().numpy())
                val_labels.extend(labels.cpu().numpy())
                
                # Calculate predicted scores
                scores_pred = model.predict_score(outputs['logits'])
                val_scores_pred.extend(scores_pred.cpu().numpy())
                val_scores_true.extend(scores_true.numpy())
        
        val_loss /= len(val_loader)
        val_acc = accuracy_score(val_labels, val_preds)
        val_rmse = np.sqrt(np.mean((np.array(val_scores_pred) - np.array(val_scores_true))**2))
        
        # Update history
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['train_acc'].append(train_acc)
        history['val_acc'].append(val_acc)
        history['val_rmse'].append(val_rmse)
        
        print(f"\nEpoch {epoch+1}/{epochs}")
        print(f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}")
        print(f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}, Val RMSE: {val_rmse:.4f}")
        
        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), save_path)
            print(f"Saved best model to {save_path}")
    
    return model, history, val_preds, val_labels


def plot_training_curves(history: dict, save_path: Path):
    """Plot and save training curves"""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    
    # Loss curves
    axes[0].plot(history['train_loss'], label='Train')
    axes[0].plot(history['val_loss'], label='Validation')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Training & Validation Loss')
    axes[0].legend()
    
    # Accuracy curves
    axes[1].plot(history['train_acc'], label='Train')
    axes[1].plot(history['val_acc'], label='Validation')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Accuracy')
    axes[1].set_title('Training & Validation Accuracy')
    axes[1].legend()
    
    # RMSE curve
    axes[2].plot(history['val_rmse'], label='Validation RMSE', color='green')
    axes[2].set_xlabel('Epoch')
    axes[2].set_ylabel('RMSE')
    axes[2].set_title('Validation RMSE')
    axes[2].legend()
    
    plt.tight_layout()
    plt.savefig(save_path / 'training_curves.png', dpi=150)
    plt.close()
    print(f"Training curves saved to {save_path / 'training_curves.png'}")


def plot_confusion_matrix(y_true: list, y_pred: list, save_path: Path):
    """Plot and save confusion matrix"""
    cm = confusion_matrix(y_true, y_pred)
    labels = [LABEL_TO_SCORE[i] for i in range(NUM_LABELS)]
    
    plt.figure(figsize=(12, 10))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=labels, yticklabels=labels)
    plt.xlabel('Predicted Score')
    plt.ylabel('True Score')
    plt.title('Confusion Matrix')
    plt.tight_layout()
    plt.savefig(save_path / 'confusion_matrix.png', dpi=150)
    plt.close()
    print(f"Confusion matrix saved to {save_path / 'confusion_matrix.png'}")


def main():
    parser = argparse.ArgumentParser(description='Train Grammar Scoring Model')
    parser.add_argument('--epochs', type=int, default=NUM_EPOCHS)
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE)
    parser.add_argument('--lr', type=float, default=LEARNING_RATE)
    parser.add_argument('--val-split', type=float, default=0.2)
    parser.add_argument('--resume', action='store_true', help='Resume training from saved model')
    args = parser.parse_args()
    
    # Initialize transcription service
    transcription_service = TranscriptionService()
    
    # Load data
    train_csv = DATASET_DIR / 'train.csv'
    df = load_training_data(train_csv, AUDIO_TRAIN_DIR, transcription_service)
    
    print(f"\nLoaded {len(df)} samples with transcriptions")
    print(f"Score distribution:\n{df['label'].value_counts().sort_index()}")
    
    # Split data
    train_df, val_df = train_test_split(
        df, test_size=args.val_split, random_state=42, stratify=df['label'].apply(lambda x: int(x*2))
    )
    
    # Train model
    model, history, val_preds, val_labels = train_model(
        train_df, val_df,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        resume=args.resume
    )
    
    # Save visualizations
    plot_training_curves(history, MODELS_DIR)
    plot_confusion_matrix(val_labels, val_preds, MODELS_DIR)
    
    # Save history
    with open(MODELS_DIR / 'training_history.json', 'w') as f:
        json.dump(history, f, indent=2)
    
    print("\nTraining complete!")
    print(f"Final Val Accuracy: {history['val_acc'][-1]:.4f}")
    print(f"Final Val RMSE: {history['val_rmse'][-1]:.4f}")


if __name__ == "__main__":
    main()
