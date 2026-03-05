"""
DeBERTa-v3 Grammar Scoring Model
"""
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel, AutoConfig
from typing import List, Dict, Optional, Tuple
import numpy as np
from pathlib import Path

from config import (
    MODEL_NAME, NUM_LABELS, MAX_LENGTH, BATCH_SIZE,
    MODELS_DIR, SCORE_TO_LABEL, LABEL_TO_SCORE
)


class GrammarDataset(Dataset):
    """Dataset for grammar scoring"""
    
    def __init__(self, texts: List[str], labels: Optional[List[float]] = None,
                 tokenizer=None, max_length: int = MAX_LENGTH):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = self.texts[idx]
        
        encoding = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding='max_length',
            return_tensors='pt'
        )
        
        item = {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0)
        }
        
        if self.labels is not None:
            # Convert score to label index
            score = float(self.labels[idx])
            if np.isnan(score):
                score = 0.0
            score = max(0.0, min(5.0, score))
            score = round(score * 2) / 2
            label_index = SCORE_TO_LABEL.get(score, 0)
            item['labels'] = torch.tensor(label_index, dtype=torch.long)
            item['score'] = torch.tensor(score, dtype=torch.float)
        
        return item


class GrammarScoringModel(nn.Module):
    """DeBERTa-based grammar scoring classifier"""
    
    def __init__(self, model_name: str = MODEL_NAME, num_labels: int = NUM_LABELS,
                 dropout: float = 0.1):
        super().__init__()
        
        self.config = AutoConfig.from_pretrained(model_name)
        self.encoder = AutoModel.from_pretrained(model_name)
        
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(self.config.hidden_size, num_labels)
        
        # Initialize classifier weights
        nn.init.xavier_uniform_(self.classifier.weight)
        nn.init.zeros_(self.classifier.bias)
    
    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor,
                labels: Optional[torch.Tensor] = None) -> Dict[str, torch.Tensor]:
        
        outputs = self.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        
        # Use [CLS] token representation
        pooled = outputs.last_hidden_state[:, 0, :]
        # Ensure pooled is float32 for classifier
        pooled = pooled.float()
        pooled = self.dropout(pooled)
        
        logits = self.classifier(pooled)
        
        result = {'logits': logits}
        
        if labels is not None:
            loss_fn = nn.CrossEntropyLoss()
            result['loss'] = loss_fn(logits, labels)
        
        return result
    
    def predict_score(self, logits: torch.Tensor) -> torch.Tensor:
        """Convert logits to grammar scores"""
        probs = torch.softmax(logits, dim=-1)
        
        # Weighted average of scores
        scores = torch.tensor([LABEL_TO_SCORE[i] for i in range(NUM_LABELS)], 
                             device=logits.device, dtype=torch.float)
        predicted_scores = (probs * scores).sum(dim=-1)
        
        return predicted_scores


class GrammarScorer:
    """High-level interface for grammar scoring"""
    
    def __init__(self, model_path: Optional[str | Path] = None,
                 device: Optional[str] = None):
        """
        Initialize scorer
        
        Args:
            model_path: Path to trained model weights
            device: Device to use (cpu, cuda)
        """
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = GrammarScoringModel()
        
        if model_path:
            self.load_model(model_path)
        
        # Convert model to float32 for consistency
        self.model = self.model.float()
        self.model.to(self.device)
        self.model.eval()
    
    def load_model(self, model_path: str | Path) -> None:
        """Load model weights from file"""
        model_path = Path(model_path)
        if model_path.exists():
            state_dict = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            print(f"Model loaded from {model_path}")
        else:
            print(f"Warning: Model file not found at {model_path}")
    
    def save_model(self, model_path: str | Path) -> None:
        """Save model weights to file"""
        model_path = Path(model_path)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(self.model.state_dict(), model_path)
        print(f"Model saved to {model_path}")
    
    def score_text(self, text: str) -> Dict:
        """
        Score a single text for grammatical quality
        
        Args:
            text: Transcript text to score
            
        Returns:
            Dictionary with score and confidence
        """
        self.model.eval()
        
        encoding = self.tokenizer(
            text,
            truncation=True,
            max_length=MAX_LENGTH,
            padding='max_length',
            return_tensors='pt'
        ).to(self.device)
        
        # Ensure input tensors match model dtype
        input_ids = encoding['input_ids'].to(self.device).long()
        attention_mask = encoding['attention_mask'].to(self.device).long()
        
        with torch.no_grad():
            try:
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask
                )
            except Exception as e:
                print(f"Error in model forward pass: {e}")
                print(f"input_ids dtype: {input_ids.dtype}, device: {input_ids.device}")
                print(f"attention_mask dtype: {attention_mask.dtype}, device: {attention_mask.device}")
                raise
            
            logits = outputs['logits']
            probs = torch.softmax(logits, dim=-1)
            
            # Get predicted continuous score
            raw_score = self.model.predict_score(logits).item()
            # Ensure it is constrained between 0 and 5
            score = max(0.0, min(5.0, raw_score))
            
            # Get predicted class (bucket)
            pred_class = torch.argmax(probs, dim=-1).item()
            confidence = probs[0, pred_class].item()
        
        return {
            'score': round(score, 2),  # Returns precise scores like 4.23
            'predicted_class': LABEL_TO_SCORE[pred_class],
            'confidence': round(confidence, 3),
            'class_probabilities': {
                LABEL_TO_SCORE[i]: round(probs[0, i].item(), 3)
                for i in range(NUM_LABELS)
            }
        }
    
    def score_batch(self, texts: List[str], batch_size: int = BATCH_SIZE) -> List[Dict]:
        """
        Score multiple texts
        
        Args:
            texts: List of transcript texts to score
            batch_size: Batch size for processing
            
        Returns:
            List of score dictionaries
        """
        dataset = GrammarDataset(texts, tokenizer=self.tokenizer)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
        
        all_results = []
        self.model.eval()
        
        with torch.no_grad():
            for batch in dataloader:
                input_ids = batch['input_ids'].to(self.device).long()
                attention_mask = batch['attention_mask'].to(self.device).long()
                
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                logits = outputs['logits']
                probs = torch.softmax(logits, dim=-1)
                scores = self.model.predict_score(logits)
                
                for i in range(len(scores)):
                    raw_score = scores[i].item()
                    score = max(0.0, min(5.0, raw_score))
                    pred_class = torch.argmax(probs[i]).item()
                    all_results.append({
                        'score': round(score, 2), # precise score
                        'predicted_class': LABEL_TO_SCORE[pred_class],
                        'confidence': round(probs[i, pred_class].item(), 3)
                    })
        
        return all_results


# Global scorer instance
_scorer = None

def get_scorer(model_path: Optional[str | Path] = None) -> GrammarScorer:
    """Get or create global scorer instance"""
    global _scorer
    if _scorer is None:
        default_path = MODELS_DIR / "deberta_classifier.pt"
        _scorer = GrammarScorer(model_path or default_path)
    return _scorer


if __name__ == "__main__":
    # Test model
    scorer = GrammarScorer()
    
    test_texts = [
        "I am going to the store to buy some groceries.",
        "He go store buy food yesterday morning.",
        "The quick brown fox jumps over the lazy dog."
    ]
    
    for text in test_texts:
        result = scorer.score_text(text)
        print(f"Text: {text[:50]}...")
        print(f"Score: {result['score']}, Confidence: {result['confidence']}")
        print()
