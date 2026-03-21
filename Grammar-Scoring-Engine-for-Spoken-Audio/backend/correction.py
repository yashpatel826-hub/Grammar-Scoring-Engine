"""
Grammar correction service for transcript text.
"""

from __future__ import annotations

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
                corrected_chunks.append(generated if generated else chunk)

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
