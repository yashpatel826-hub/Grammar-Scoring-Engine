"""
Audio preprocessing module for Grammar Scoring Engine
Handles audio normalization, VAD-based silence trimming, and format conversion
"""
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
from typing import Tuple, Optional
import warnings
warnings.filterwarnings("ignore")

from config import SAMPLE_RATE, MAX_AUDIO_DURATION, MIN_AUDIO_DURATION


def load_audio(audio_path: str | Path, sr: int = SAMPLE_RATE) -> Tuple[np.ndarray, int]:
    """
    Load audio file and resample to target sample rate
    
    Args:
        audio_path: Path to audio file
        sr: Target sample rate
        
    Returns:
        Tuple of (audio_array, sample_rate)
    """
    audio, original_sr = librosa.load(str(audio_path), sr=sr, mono=True)
    return audio, sr


def peak_normalize(audio: np.ndarray, target_db: float = -3.0) -> np.ndarray:
    """
    Apply peak normalization to audio signal
    
    Args:
        audio: Audio signal array
        target_db: Target peak level in dB
        
    Returns:
        Normalized audio array
    """
    peak = np.max(np.abs(audio))
    if peak > 0:
        target_amplitude = 10 ** (target_db / 20)
        audio = audio * (target_amplitude / peak)
    return audio


def trim_silence(audio: np.ndarray, sr: int = SAMPLE_RATE, 
                 top_db: int = 25, frame_length: int = 2048,
                 hop_length: int = 512) -> np.ndarray:
    """
    Remove silence from beginning and end of audio using VAD
    
    Args:
        audio: Audio signal array
        sr: Sample rate
        top_db: Threshold in dB below which signal is considered silence
        frame_length: Frame length for analysis
        hop_length: Hop length for analysis
        
    Returns:
        Trimmed audio array
    """
    # Use librosa's trim function for VAD-based silence removal
    trimmed_audio, _ = librosa.effects.trim(
        audio, 
        top_db=top_db,
        frame_length=frame_length,
        hop_length=hop_length
    )
    return trimmed_audio


def limit_duration(audio: np.ndarray, sr: int = SAMPLE_RATE,
                   max_duration: float = MAX_AUDIO_DURATION) -> np.ndarray:
    """
    Limit audio to maximum duration
    
    Args:
        audio: Audio signal array
        sr: Sample rate
        max_duration: Maximum duration in seconds
        
    Returns:
        Clipped audio array
    """
    max_samples = int(max_duration * sr)
    if len(audio) > max_samples:
        audio = audio[:max_samples]
    return audio


def preprocess_audio(audio_path: str | Path, 
                     normalize: bool = True,
                     trim: bool = True,
                     limit: bool = True) -> Tuple[np.ndarray, int]:
    """
    Complete audio preprocessing pipeline
    
    Args:
        audio_path: Path to audio file
        normalize: Apply peak normalization
        trim: Apply silence trimming
        limit: Apply duration limiting
        
    Returns:
        Tuple of (preprocessed_audio, sample_rate)
    """
    # Load audio
    audio, sr = load_audio(audio_path)
    
    # Apply preprocessing steps
    if trim:
        audio = trim_silence(audio, sr)
    
    if normalize:
        audio = peak_normalize(audio)
    
    if limit:
        audio = limit_duration(audio, sr)
    
    return audio, sr


def save_audio(audio: np.ndarray, output_path: str | Path, 
               sr: int = SAMPLE_RATE) -> None:
    """
    Save audio to file
    
    Args:
        audio: Audio signal array
        output_path: Path to save audio
        sr: Sample rate
    """
    sf.write(str(output_path), audio, sr)


def get_audio_duration(audio_path: str | Path) -> float:
    """
    Get duration of audio file in seconds
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Duration in seconds
    """
    return librosa.get_duration(path=str(audio_path))


def validate_audio(audio_path: str | Path) -> Tuple[bool, str]:
    """
    Validate audio file for processing
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Tuple of (is_valid, message)
    """
    try:
        duration = get_audio_duration(audio_path)
        
        if duration < MIN_AUDIO_DURATION:
            return False, f"Audio too short: {duration:.1f}s (minimum: {MIN_AUDIO_DURATION}s)"
        
        if duration > MAX_AUDIO_DURATION * 2:  # Allow some buffer
            return False, f"Audio too long: {duration:.1f}s (maximum: {MAX_AUDIO_DURATION * 2}s)"
        
        # Try loading to verify format
        audio, _ = load_audio(audio_path)
        if len(audio) == 0:
            return False, "Audio file appears to be empty"
        
        return True, "Audio file is valid"
        
    except Exception as e:
        return False, f"Error reading audio file: {str(e)}"


if __name__ == "__main__":
    # Test preprocessing
    import sys
    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
        is_valid, message = validate_audio(audio_path)
        print(f"Validation: {message}")
        
        if is_valid:
            audio, sr = preprocess_audio(audio_path)
            print(f"Preprocessed audio: {len(audio)/sr:.2f}s at {sr}Hz")
