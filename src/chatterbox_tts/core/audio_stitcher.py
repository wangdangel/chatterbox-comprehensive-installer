"""
Audio stitching and processing utilities.
Handles combining multiple audio segments with crossfades and effects.
"""

import os
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
from typing import List, Optional, Tuple, Union
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AudioSegment:
    """Represents an audio segment for stitching."""
    file_path: Optional[str] = None
    audio_data: Optional[np.ndarray] = None
    sample_rate: int = 22050
    duration: float = 0.0
    fade_in: float = 0.0
    fade_out: float = 0.0
    volume: float = 1.0
    offset: float = 0.0


class AudioStitcher:
    """Handles audio segment stitching and processing."""
    
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
    
    def stitch_segments(
        self,
        segments: List[AudioSegment],
        crossfade_duration: float = 0.5,
        output_path: Optional[str] = None
    ) -> Tuple[np.ndarray, int]:
        """
        Stitch multiple audio segments together with crossfades.
        
        Args:
            segments: List of audio segments to stitch
            crossfade_duration: Duration of crossfade in seconds
            output_path: Optional path to save the result
            
        Returns:
            Tuple of (audio_data, sample_rate)
        """
        if not segments:
            raise ValueError("No segments provided")
        
        # Load audio data for segments that only have file paths
        loaded_segments = []
        for segment in segments:
            if segment.file_path and segment.audio_data is None:
                audio_data, sr = self._load_audio(segment.file_path)
                if sr != self.sample_rate:
                    audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=self.sample_rate)
                segment.audio_data = audio_data
                segment.sample_rate = self.sample_rate
                segment.duration = len(audio_data) / self.sample_rate
            
            if segment.audio_data is not None:
                loaded_segments.append(segment)
        
        if not loaded_segments:
            raise ValueError("No valid audio segments")
        
        # Calculate total duration
        total_duration = self._calculate_total_duration(loaded_segments, crossfade_duration)
        
        # Create output array
        total_samples = int(total_duration * self.sample_rate)
        output_audio = np.zeros(total_samples, dtype=np.float32)
        
        # Stitch segments with crossfades
        current_position = 0
        
        for i, segment in enumerate(loaded_segments):
            segment_samples = len(segment.audio_data)
            segment_duration = segment_samples / self.sample_rate
            
            # Apply volume adjustment
            segment_audio = segment.audio_data * segment.volume
            
            # Apply fade in/out
            if segment.fade_in > 0:
                fade_samples = int(segment.fade_in * self.sample_rate)
                fade_in = np.linspace(0, 1, fade_samples)
                segment_audio[:fade_samples] *= fade_in
            
            if segment.fade_out > 0:
                fade_samples = int(segment.fade_out * self.sample_rate)
                fade_out = np.linspace(1, 0, fade_samples)
                segment_audio[-fade_samples:] *= fade_out
            
            # Handle crossfades
            if i > 0 and crossfade_duration > 0:
                crossfade_samples = int(crossfade_duration * self.sample_rate)
                
                # Calculate overlap region
                overlap_start = max(0, current_position - crossfade_samples)
                overlap_end = current_position + segment_samples
                
                # Create crossfade envelope
                if overlap_start < current_position:
                    fade_out = np.linspace(1, 0, crossfade_samples)
                    fade_in = np.linspace(0, 1, crossfade_samples)
                    
                    # Apply crossfade to overlapping region
                    existing_audio = output_audio[overlap_start:current_position]
                    new_audio = segment_audio[:crossfade_samples]
                    
                    # Mix with crossfade
                    mixed = existing_audio * fade_out + new_audio * fade_in
                    output_audio[overlap_start:current_position] = mixed
                    
                    # Add remaining audio
                    remaining_audio = segment_audio[crossfade_samples:]
                    end_pos = current_position + len(remaining_audio)
                    if end_pos <= len(output_audio):
                        output_audio[current_position:end_pos] = remaining_audio
                    
                    current_position = end_pos
                else:
                    # No overlap, just add the segment
                    end_pos = current_position + segment_samples
                    if end_pos <= len(output_audio):
                        output_audio[current_position:end_pos] = segment_audio
                    current_position = end_pos
            else:
                # No crossfade, just add the segment
                end_pos = current_position + segment_samples
                if end_pos <= len(output_audio):
                    output_audio[current_position:end_pos] = segment_audio
                current_position = end_pos
        
        # Normalize audio
        max_amplitude = np.max(np.abs(output_audio))
        if max_amplitude > 0:
            output_audio = output_audio / max_amplitude * 0.95
        
        # Save if output path provided
        if output_path:
            self._save_audio(output_audio, output_path)
        
        return output_audio, self.sample_rate
    
    def apply_effects(
        self,
        audio_data: np.ndarray,
        speed: float = 1.0,
        pitch: float = 1.0,
        volume: float = 1.0
    ) -> np.ndarray:
        """
        Apply audio effects to the input audio.
        
        Args:
            audio_data: Input audio data
            speed: Speed multiplier (0.5 = half speed, 2.0 = double speed)
            pitch: Pitch multiplier (0.5 = half pitch, 2.0 = double pitch)
            volume: Volume multiplier
            
        Returns:
            Processed audio data
        """
        if speed <= 0 or pitch <= 0:
            raise ValueError("Speed and pitch must be positive")
        
        processed_audio = audio_data
        
        # Apply speed change (affects both speed and pitch)
        if speed != 1.0:
            processed_audio = librosa.effects.time_stretch(processed_audio, rate=speed)
        
        # Apply pitch change (independent of speed)
        if pitch != 1.0:
            processed_audio = librosa.effects.pitch_shift(
                processed_audio,
                sr=self.sample_rate,
                n_steps=12 * np.log2(pitch)
            )
        
        # Apply volume
        if volume != 1.0:
            processed_audio = processed_audio * volume
        
        # Ensure audio stays in valid range
        processed_audio = np.clip(processed_audio, -1.0, 1.0)
        
        return processed_audio
    
    def add_silence(
        self,
        audio_data: np.ndarray,
        duration: float,
        position: str = "end"
    ) -> np.ndarray:
        """
        Add silence to audio.
        
        Args:
            audio_data: Input audio data
            duration: Duration of silence in seconds
            position: Where to add silence ("start", "end", or "both")
            
        Returns:
            Audio with added silence
        """
        silence_samples = int(duration * self.sample_rate)
        silence = np.zeros(silence_samples, dtype=audio_data.dtype)
        
        if position == "start":
            return np.concatenate([silence, audio_data])
        elif position == "end":
            return np.concatenate([audio_data, silence])
        elif position == "both":
            return np.concatenate([silence, audio_data, silence])
        else:
            raise ValueError("Position must be 'start', 'end', or 'both'")
    
    def normalize_audio(
        self,
        audio_data: np.ndarray,
        target_level: float = -3.0
    ) -> np.ndarray:
        """
        Normalize audio to target level.
        
        Args:
            audio_data: Input audio data
            target_level: Target RMS level in dB
            
        Returns:
            Normalized audio data
        """
        # Calculate RMS
        rms = np.sqrt(np.mean(audio_data ** 2))
        
        if rms > 0:
            # Convert target level to linear scale
            target_rms = 10 ** (target_level / 20)
            
            # Calculate gain
            gain = target_rms / rms
            
            # Apply gain
            normalized = audio_data * gain
            
            # Ensure we don't clip
            max_val = np.max(np.abs(normalized))
            if max_val > 1.0:
                normalized = normalized / max_val
            
            return normalized
        
        return audio_data
    
    def detect_silence(
        self,
        audio_data: np.ndarray,
        threshold: float = 0.01,
        min_duration: float = 0.1
    ) -> List[Tuple[float, float]]:
        """
        Detect silence regions in audio.
        
        Args:
            audio_data: Input audio data
            threshold: Amplitude threshold for silence
            min_duration: Minimum silence duration in seconds
            
        Returns:
            List of (start_time, end_time) tuples for silence regions
        """
        # Calculate frame energy
        frame_length = int(0.025 * self.sample_rate)  # 25ms frames
        hop_length = int(0.010 * self.sample_rate)    # 10ms hop
        
        frames = librosa.util.frame(
            audio_data,
            frame_length=frame_length,
            hop_length=hop_length
        )
        
        # Calculate RMS for each frame
        rms = np.sqrt(np.mean(frames ** 2, axis=0))
        
        # Detect silence frames
        silence_frames = rms < threshold
        
        # Find silence regions
        silence_regions = []
        min_frames = int(min_duration * self.sample_rate / hop_length)
        
        current_start = None
        frame_count = 0
        
        for i, is_silent in enumerate(silence_frames):
            if is_silent and current_start is None:
                current_start = i
                frame_count = 1
            elif is_silent and current_start is not None:
                frame_count += 1
            elif not is_silent and current_start is not None:
                if frame_count >= min_frames:
                    start_time = current_start * hop_length / self.sample_rate
                    end_time = i * hop_length / self.sample_rate
                    silence_regions.append((start_time, end_time))
                current_start = None
                frame_count = 0
        
        # Handle case where audio ends with silence
        if current_start is not None and frame_count >= min_frames:
            start_time = current_start * hop_length / self.sample_rate
            end_time = len(audio_data) / self.sample_rate
            silence_regions.append((start_time, end_time))
        
        return silence_regions
    
    def trim_silence(
        self,
        audio_data: np.ndarray,
        threshold: float = 0.01,
        min_duration: float = 0.1
    ) -> np.ndarray:
        """
        Trim silence from beginning and end of audio.
        
        Args:
            audio_data: Input audio data
            threshold: Amplitude threshold for silence
            min_duration: Minimum silence duration to trim
            
        Returns:
            Trimmed audio data
        """
        silence_regions = self.detect_silence(audio_data, threshold, min_duration)
        
        if not silence_regions:
            return audio_data
        
        # Find start and end of non-silence
        start_time = 0.0
        end_time = len(audio_data) / self.sample_rate
        
        # Check if first region is silence at start
        if silence_regions and silence_regions[0][0] == 0.0:
            start_time = silence_regions[0][1]
        
        # Check if last region is silence at end
        if silence_regions and silence_regions[-1][1] >= end_time - 0.01:
            end_time = silence_regions[-1][0]
        
        # Convert to samples
        start_sample = int(start_time * self.sample_rate)
        end_sample = int(end_time * self.sample_rate)
        
        return audio_data[start_sample:end_sample]
    
    def _load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        """Load audio from file."""
        audio_data, sample_rate = librosa.load(file_path, sr=None)
        return audio_data, sample_rate
    
    def _save_audio(self, audio_data: np.ndarray, file_path: str):
        """Save audio to file."""
        sf.write(file_path, audio_data, self.sample_rate)
    
    def _calculate_total_duration(
        self,
        segments: List[AudioSegment],
        crossfade_duration: float
    ) -> float:
        """Calculate total duration including crossfades."""
        total_duration = 0.0
        
        for i, segment in enumerate(segments):
            if i == 0:
                total_duration += segment.duration
            else:
                total_duration += segment.duration - crossfade_duration
        
        return max(0, total_duration)


# Global audio stitcher instance
audio_stitcher = AudioStitcher()