"""
Transcription module using Whisper for Speech-to-Text
"""
import json
from pathlib import Path
from typing import Dict, Optional, List
import hashlib
import numpy as np
import whisper

from config import (
    WHISPER_MODEL, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE,
    TRANSCRIPTS_DIR, SAMPLE_RATE
)
from preprocessing import preprocess_audio


class TranscriptionService:
    """Service for transcribing audio files using Whisper"""
    
    def __init__(self, model_size: str = WHISPER_MODEL,
                 device: str = WHISPER_DEVICE,
                 compute_type: str = WHISPER_COMPUTE_TYPE):
        """
        Initialize the transcription service
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to run model on (cpu, cuda)
            compute_type: Compute type (float32, float16, int8)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None
    
    @property
    def model(self):
        """Lazy load the Whisper model"""
        if self._model is None:
            print(f"Loading Whisper model: {self.model_size} on {self.device}...")
            self._model = whisper.load_model(
                self.model_size,
                device=self.device
            )
            print("Whisper model loaded successfully!")
        return self._model
    
    def _get_cache_path(self, audio_path: str | Path) -> Path:
        """Generate cache path for transcription"""
        audio_path = Path(audio_path)
        # Create hash from filename and file size for cache key
        file_stat = audio_path.stat()
        cache_key = f"{audio_path.name}_{file_stat.st_size}_{file_stat.st_mtime}"
        cache_hash = hashlib.md5(cache_key.encode()).hexdigest()[:12]
        return TRANSCRIPTS_DIR / f"{audio_path.stem}_{cache_hash}.json"
    
    def _load_cached(self, cache_path: Path) -> Optional[Dict]:
        """Load cached transcription if exists"""
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return None
        return None
    
    def _save_cache(self, cache_path: Path, data: Dict) -> None:
        """Save transcription to cache"""
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _transcribe_with_whisper(self, audio_input) -> Dict:
        """Run whisper transcription with conservative settings to reduce hallucinations."""
        return self.model.transcribe(
            audio_input,
            language="en",
            verbose=False,
            temperature=0.0,
            condition_on_previous_text=False,
            no_speech_threshold=0.45,
            logprob_threshold=-1.0,
            compression_ratio_threshold=2.4,
            fp16=(self.device == "cuda")
        )

    def _try_transcription_variants(self, audio: np.ndarray, audio_path: Path) -> Dict:
        """Try progressively boosted audio variants to recover quiet speech."""
        attempts: List[np.ndarray] = [audio]

        peak = float(np.max(np.abs(audio))) if len(audio) else 0.0
        if peak > 0:
            attempts.append(np.clip(audio * min(3.0, 0.95 / peak), -1.0, 1.0))
            attempts.append(np.clip(audio * min(8.0, 0.95 / peak), -1.0, 1.0))

        best_result = {"text": "", "segments": []}

        def _is_usable_text(text: str) -> bool:
            words = [w for w in text.strip().split() if w]
            # Grammar scoring is sentence-based; single-word outputs are usually low-signal hallucinations.
            return len(words) >= 2

        for idx, candidate in enumerate(attempts):
            try:
                result = self._transcribe_with_whisper(candidate)
                text = result.get("text", "").strip()
                if _is_usable_text(text):
                    print(f"Transcription succeeded on attempt {idx + 1}")
                    return result

                if text and len(text) > len(best_result.get("text", "")):
                    best_result = result
                elif len(result.get("segments", [])) > len(best_result.get("segments", [])):
                    best_result = result
            except Exception as e:
                print(f"Transcription attempt {idx + 1} failed: {e}")

        # Final fallback through file path (lets whisper/ffmpeg decode directly)
        try:
            fallback = self._transcribe_with_whisper(str(audio_path))
            fallback_text = fallback.get("text", "").strip()
            if _is_usable_text(fallback_text):
                print("Transcription succeeded via file-path fallback")
                return fallback
            if fallback_text and len(fallback_text) > len(best_result.get("text", "")):
                best_result = fallback
            elif len(fallback.get("segments", [])) > len(best_result.get("segments", [])):
                best_result = fallback
        except Exception as e:
            print(f"File-path fallback failed: {e}")

        return best_result
    
    def transcribe(self, audio_path: str | Path, 
                   use_cache: bool = True,
                   preprocess: bool = True) -> Dict:
        """
        Transcribe audio file to text
        
        Args:
            audio_path: Path to audio file
            use_cache: Whether to use cached transcription
            preprocess: Whether to preprocess audio before transcription
            
        Returns:
            Dictionary with transcript and metadata
        """
        audio_path = Path(audio_path)
        
        # Check cache first
        if use_cache:
            cache_path = self._get_cache_path(audio_path)
            cached = self._load_cached(cache_path)
            if cached:
                return cached
        
        # Load and preprocess audio for more reliable speech detection
        try:
            audio, sr = preprocess_audio(audio_path, normalize=True, trim=True, limit=True)
            print(f"Audio preprocessed: {len(audio)} samples at {sr}Hz")
        except Exception as e:
            print(f"Error preprocessing audio: {e}")
            raise

        if len(audio) == 0:
            result = {"text": "", "language": "en", "duration": 0, "segments": []}
        else:
            result = self._try_transcription_variants(audio, audio_path)
        
        # Format output to match expected structure
        formatted_result = {
            "text": result.get("text", "").strip(),
            "language": result.get("language", "en"),
            "language_probability": 0.95,
            "duration": result.get("duration", len(audio) / sr if sr else 0),
            "segments": [
                {
                    "start": round(seg.get("start", 0), 2),
                    "end": round(seg.get("end", 0), 2),
                    "text": seg.get("text", "").strip()
                }
                for seg in result.get("segments", [])
            ]
        }
        
        # Save to cache
        if use_cache:
            self._save_cache(cache_path, formatted_result)
        
        return formatted_result
    
    def transcribe_batch(self, audio_paths: List[str | Path],
                         use_cache: bool = True) -> List[Dict]:
        """
        Transcribe multiple audio files
        
        Args:
            audio_paths: List of paths to audio files
            use_cache: Whether to use cached transcriptions
            
        Returns:
            List of transcription dictionaries
        """
        results = []
        for path in audio_paths:
            try:
                result = self.transcribe(path, use_cache=use_cache)
                result["filename"] = Path(path).name
                result["success"] = True
            except Exception as e:
                result = {
                    "filename": Path(path).name,
                    "success": False,
                    "error": str(e)
                }
            results.append(result)
        return results


# Global service instance
_transcription_service = None

def get_transcription_service() -> TranscriptionService:
    """Get or create global transcription service instance"""
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = TranscriptionService()
    return _transcription_service


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        service = TranscriptionService()
        result = service.transcribe(sys.argv[1])
        print(f"Transcript: {result['text']}")
        print(f"Duration: {result['duration']}s")
        print(f"Language: {result['language']} ({result['language_probability']:.1%})")
