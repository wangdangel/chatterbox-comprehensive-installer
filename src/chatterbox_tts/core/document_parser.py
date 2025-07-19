"""
Document parsing and processing for TTS.
Handles text segmentation, JSON processing, and document analysis.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TextSegment:
    """Represents a segment of text for TTS processing."""
    text: str
    index: int
    start_pos: int
    end_pos: int
    metadata: Dict[str, Any]
    voice_id: Optional[str] = None
    speed: Optional[float] = None
    pitch: Optional[float] = None


@dataclass
class DocumentInfo:
    """Information about a processed document."""
    filename: str
    total_chars: int
    total_segments: int
    segments: List[TextSegment]
    metadata: Dict[str, Any]


class DocumentParser:
    """Handles document parsing and text segmentation for TTS."""
    
    def __init__(self, chunk_size: int = 1000, overlap_size: int = 50):
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.max_chunk_size = 2000
    
    def parse_file(self, file_path: Union[str, Path]) -> DocumentInfo:
        """Parse a file and return document information."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine file type and parse accordingly
        if file_path.suffix.lower() == '.json':
            return self._parse_json_file(file_path)
        elif file_path.suffix.lower() in ['.txt', '.md', '.text']:
            return self._parse_text_file(file_path)
        else:
            # Try to read as text
            return self._parse_text_file(file_path)
    
    def parse_text(self, text: str, filename: str = "input.txt") -> DocumentInfo:
        """Parse raw text and return document information."""
        segments = self._segment_text(text)
        
        return DocumentInfo(
            filename=filename,
            total_chars=len(text),
            total_segments=len(segments),
            segments=segments,
            metadata={
                "source": "text_input",
                "type": "raw_text"
            }
        )
    
    def _parse_json_file(self, file_path: Path) -> DocumentInfo:
        """Parse JSON file with TTS configuration."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON formats
            if isinstance(data, dict):
                if 'text' in data:
                    # Simple format: {"text": "...", "voice_id": "...", ...}
                    text = data['text']
                    voice_id = data.get('voice_id')
                    speed = data.get('speed')
                    pitch = data.get('pitch')
                    
                    segments = self._segment_text(text)
                    for segment in segments:
                        if voice_id:
                            segment.voice_id = voice_id
                        if speed:
                            segment.speed = speed
                        if pitch:
                            segment.pitch = pitch
                    
                elif 'segments' in data:
                    # Advanced format: {"segments": [...]}
                    segments = self._parse_segments(data['segments'])
                    text = ''.join([s.text for s in segments])
                    
                else:
                    # Assume it's a single text field
                    text = str(data)
                    segments = self._segment_text(text)
                    
            elif isinstance(data, list):
                # Array format: ["text1", "text2", ...]
                text = ' '.join(str(item) for item in data)
                segments = self._segment_text(text)
                
            else:
                # Fallback to string conversion
                text = str(data)
                segments = self._segment_text(text)
            
            return DocumentInfo(
                filename=file_path.name,
                total_chars=len(text),
                total_segments=len(segments),
                segments=segments,
                metadata={
                    "source": "json_file",
                    "type": "structured",
                    "file_size": file_path.stat().st_size
                }
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            # Fallback to text parsing
            return self._parse_text_file(file_path)
    
    def _parse_text_file(self, file_path: Path) -> DocumentInfo:
        """Parse plain text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            segments = self._segment_text(text)
            
            return DocumentInfo(
                filename=file_path.name,
                total_chars=len(text),
                total_segments=len(segments),
                segments=segments,
                metadata={
                    "source": "text_file",
                    "type": "plain_text",
                    "file_size": file_path.stat().st_size
                }
            )
            
        except UnicodeDecodeError:
            # Try different encodings
            for encoding in ['utf-8-sig', 'latin-1', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        text = f.read()
                    
                    segments = self._segment_text(text)
                    
                    return DocumentInfo(
                        filename=file_path.name,
                        total_chars=len(text),
                        total_segments=len(segments),
                        segments=segments,
                        metadata={
                            "source": "text_file",
                            "type": "plain_text",
                            "encoding": encoding,
                            "file_size": file_path.stat().st_size
                        }
                    )
                except UnicodeDecodeError:
                    continue
            
            raise ValueError(f"Unable to decode file: {file_path}")
    
    def _parse_segments(self, segments_data: List[Dict[str, Any]]) -> List[TextSegment]:
        """Parse pre-defined segments from JSON."""
        segments = []
        
        for i, segment_data in enumerate(segments_data):
            segment = TextSegment(
                text=segment_data.get('text', ''),
                index=i,
                start_pos=segment_data.get('start_pos', 0),
                end_pos=segment_data.get('end_pos', 0),
                metadata=segment_data.get('metadata', {}),
                voice_id=segment_data.get('voice_id'),
                speed=segment_data.get('speed'),
                pitch=segment_data.get('pitch')
            )
            segments.append(segment)
        
        return segments
    
    def _segment_text(self, text: str) -> List[TextSegment]:
        """Segment text into chunks for TTS processing."""
        if not text.strip():
            return []
        
        # Clean and normalize text
        text = self._clean_text(text)
        
        # If text is short enough, return as single segment
        if len(text) <= self.chunk_size:
            return [TextSegment(
                text=text,
                index=0,
                start_pos=0,
                end_pos=len(text),
                metadata={"type": "single_segment"}
            )]
        
        # Split into sentences first
        sentences = self._split_into_sentences(text)
        
        # Group sentences into chunks
        chunks = self._group_sentences_into_chunks(sentences)
        
        # Create segments with overlap
        segments = []
        for i, chunk in enumerate(chunks):
            start_pos = max(0, chunk['start_pos'] - self.overlap_size if i > 0 else 0)
            end_pos = min(len(text), chunk['end_pos'] + self.overlap_size if i < len(chunks) - 1 else len(text))
            
            segment_text = text[start_pos:end_pos].strip()
            
            segment = TextSegment(
                text=segment_text,
                index=i,
                start_pos=start_pos,
                end_pos=end_pos,
                metadata={
                    "type": "chunk",
                    "sentence_count": len(chunk['sentences']),
                    "original_start": chunk['start_pos'],
                    "original_end": chunk['end_pos']
                }
            )
            segments.append(segment)
        
        return segments
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace("'", "'").replace("'", "'")
        
        # Remove extra newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _split_into_sentences(self, text: str) -> List[Dict[str, Any]]:
        """Split text into sentences with positions."""
        # Simple sentence splitting - can be enhanced with NLP libraries
        sentence_endings = r'[.!?]+'
        
        sentences = []
        last_end = 0
        
        for match in re.finditer(sentence_endings, text):
            end_pos = match.end()
            sentence = text[last_end:end_pos].strip()
            
            if sentence:
                sentences.append({
                    'text': sentence,
                    'start_pos': last_end,
                    'end_pos': end_pos
                })
            
            last_end = end_pos
        
        # Handle remaining text
        if last_end < len(text):
            remaining = text[last_end:].strip()
            if remaining:
                sentences.append({
                    'text': remaining,
                    'start_pos': last_end,
                    'end_pos': len(text)
                })
        
        return sentences
    
    def _group_sentences_into_chunks(self, sentences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group sentences into chunks of appropriate size."""
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence['text'])
            
            # Start new chunk if current would be too large
            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunks.append({
                    'sentences': current_chunk,
                    'text': ' '.join([s['text'] for s in current_chunk]),
                    'start_pos': current_chunk[0]['start_pos'],
                    'end_pos': current_chunk[-1]['end_pos']
                })
                current_chunk = []
                current_length = 0
            
            current_chunk.append(sentence)
            current_length += sentence_length
        
        # Add remaining sentences
        if current_chunk:
            chunks.append({
                'sentences': current_chunk,
                'text': ' '.join([s['text'] for s in current_chunk]),
                'start_pos': current_chunk[0]['start_pos'],
                'end_pos': current_chunk[-1]['end_pos']
            })
        
        return chunks
    
    def analyze_document(self, text: str) -> Dict[str, Any]:
        """Analyze document characteristics."""
        # Basic text analysis
        char_count = len(text)
        word_count = len(text.split())
        sentence_count = len(re.split(r'[.!?]+', text))
        
        # Estimate reading time (average 150 words per minute)
        reading_time_minutes = word_count / 150
        
        # Detect language (simple heuristic)
        language = "en"  # Default to English
        
        return {
            "character_count": char_count,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "estimated_reading_time_minutes": round(reading_time_minutes, 1),
            "language": language,
            "requires_segmentation": char_count > self.chunk_size
        }
    
    def create_processing_plan(self, document: DocumentInfo) -> Dict[str, Any]:
        """Create a processing plan for the document."""
        analysis = self.analyze_document(''.join([s.text for s in document.segments]))
        
        return {
            "document": document.filename,
            "total_segments": document.total_segments,
            "estimated_processing_time": document.total_segments * 2,  # 2 seconds per segment
            "requires_stitching": document.total_segments > 1,
            "recommended_chunk_size": self.chunk_size,
            "analysis": analysis
        }