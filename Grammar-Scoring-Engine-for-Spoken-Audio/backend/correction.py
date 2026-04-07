"""
Grammar correction service for transcript text.
"""

from __future__ import annotations

import difflib
import re
from typing import Any, Dict, List

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from error_analysis import analyze_correction


class GrammarCorrector:
    """Grammar correction using an instruction-tuned T5 model."""

    def __init__(self, model_name: str = "vennify/t5-base-grammar-correction"):
        self.model_name = model_name
        self._tokenizer = None
        self._model = None
        self._is_available = False
        self._init_error = ""
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._load_pipeline()

    def _load_pipeline(self) -> None:
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            self._model.to(self._device)
            self._model.eval()
            self._is_available = True
        except Exception as exc:
            self._init_error = str(exc)
            self._tokenizer = None
            self._model = None
            self._is_available = False

    @staticmethod
    def _chunk_text(text: str, max_chunk_chars: int = 450) -> List[str]:
        # Keep sentence boundaries where possible to improve correction quality.
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        chunks: List[str] = []
        current = ""

        for sentence in sentences:
            if not sentence:
                continue

            candidate = f"{current} {sentence}".strip()
            if len(candidate) <= max_chunk_chars:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                current = sentence

        if current:
            chunks.append(current)

        return chunks if chunks else [text]

    @staticmethod
    def _tokenize_words(text: str) -> List[str]:
        return re.findall(r"[A-Za-z0-9']+", text.lower())

    @classmethod
    def _is_destructive_rewrite(cls, original: str, candidate: str) -> bool:
        """Reject rewrites that remove too much lexical content from the original."""
        original_tokens = cls._tokenize_words(original)
        candidate_tokens = cls._tokenize_words(candidate)

        if not original_tokens:
            return False
        if not candidate_tokens:
            return True

        length_ratio = len(candidate_tokens) / max(1, len(original_tokens))

        # Grammar correction should not remove large parts of long text.
        if len(original_tokens) >= 40 and length_ratio < 0.72:
            return True

        # Strong length shrink can indicate content dropping.
        if len(original_tokens) >= 8 and len(candidate_tokens) < max(4, int(0.55 * len(original_tokens))):
            return True

        original_questions = original.count("?")
        candidate_questions = candidate.count("?")
        if original_questions >= 2 and (original_questions - candidate_questions) >= 2 and length_ratio < 0.85:
            return True

        original_vocab = set(original_tokens)
        retained_ratio = len(original_vocab.intersection(candidate_tokens)) / max(1, len(original_vocab))

        # Low overlap on sufficiently long chunks usually means a semantic rewrite/omission.
        if len(original_tokens) >= 12 and retained_ratio < 0.62:
            return True

        seq_ratio = difflib.SequenceMatcher(a=original_tokens, b=candidate_tokens, autojunk=False).ratio()
        if len(original_tokens) >= 12 and seq_ratio < 0.45:
            return True

        return False

    def correct_text(self, text: str) -> Dict[str, Any]:
        clean_text = text.strip()
        if not clean_text:
            return {
                "corrected_text": text,
                "changed": False,
                "available": self._is_available,
                "error": "Text cannot be empty",
                "errors": [],
                "suggestions": [],
                "summary": {"total_errors": 0},
            }

        if not self._is_available or self._tokenizer is None or self._model is None:
            return {
                "corrected_text": text,
                "changed": False,
                "available": False,
                "error": self._init_error or "Grammar correction model is unavailable",
                "errors": [],
                "suggestions": [],
                "summary": {"total_errors": 0},
            }

        try:
            corrected_chunks: List[str] = []
            for chunk in self._chunk_text(clean_text):
                prompt = f"grammar: {chunk}"
                encoded = self._tokenizer(
                    prompt,
                    return_tensors="pt",
                    truncation=True,
                    max_length=256,
                ).to(self._device)
                with torch.no_grad():
                    output_ids = self._model.generate(
                        **encoded,
                        max_length=256,
                        num_beams=4,
                        early_stopping=True,
                    )
                generated = self._tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()
                if not generated or self._is_destructive_rewrite(chunk, generated):
                    corrected_chunks.append(chunk)
                else:
                    corrected_chunks.append(generated)

            corrected_text = " ".join(corrected_chunks).strip()
            if not corrected_text:
                corrected_text = text

            changed = corrected_text != clean_text
            analysis = analyze_correction(clean_text, corrected_text) if changed else {
                "errors": [],
                "suggestions": [],
                "summary": {"total_errors": 0},
            }

            return {
                "corrected_text": corrected_text,
                "changed": changed,
                "available": True,
                "error": None,
                "errors": analysis.get("errors", []),
                "suggestions": analysis.get("suggestions", []),
                "summary": analysis.get("summary", {"total_errors": 0}),
            }
        except Exception as exc:
            return {
                "corrected_text": text,
                "changed": False,
                "available": True,
                "error": str(exc),
                "errors": [],
                "suggestions": [],
                "summary": {"total_errors": 0},
            }


_corrector = None


def get_corrector() -> GrammarCorrector:
    global _corrector
    if _corrector is None:
        _corrector = GrammarCorrector()
    return _corrector
