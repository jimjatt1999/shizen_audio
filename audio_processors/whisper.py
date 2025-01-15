# audio_processors/whisper.py
from faster_whisper import WhisperModel
from typing import List, Dict
import uuid
import json
from pathlib import Path

class WhisperProcessor:
    # Dictionary of supported languages with their codes
    SUPPORTED_LANGUAGES = {
        'Japanese': 'ja',
        'English': 'en',
        'Chinese': 'zh',
        'Korean': 'ko',
        'Spanish': 'es',
        'French': 'fr',
        'German': 'de',
        'Italian': 'it',
        'Russian': 'ru',
        'Portuguese': 'pt',
        # Add more languages as needed
    }

    def __init__(self, model_size: str = "base", language: str = "ja"):
        """Initialize Whisper processor"""
        print(f"Initializing Whisper with model size: {model_size}")
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        self.language = language
        
    def set_language(self, language: str):
        """Set transcription language"""
        if language in self.SUPPORTED_LANGUAGES.values():
            self.language = language
        else:
            raise ValueError(f"Unsupported language code: {language}")
        
    def transcribe(self, audio_path: str, max_segment_length: float = 15.0) -> List[Dict]:
        """Transcribe audio file and return segments"""
        try:
            print(f"Starting transcription of: {audio_path} in {self.language}")
            segments, _ = self.model.transcribe(
                audio_path,
                language=self.language,
                beam_size=5,
                word_timestamps=True
            )
            
            processed_segments = []
            for segment in segments:
                # Only add segments that have actual content
                if segment.text.strip():
                    processed_segments.append({
                        'id': str(uuid.uuid4()),
                        'start': segment.start,
                        'end': segment.end,
                        'text': segment.text.strip(),
                        'words': [{'word': w.word, 'start': w.start, 'end': w.end} 
                                for w in segment.words] if segment.words else []
                    })
            
            print(f"Generated {len(processed_segments)} segments")
            if not processed_segments:
                raise Exception("No valid segments were generated")
                
            return processed_segments
            
        except Exception as e:
            print(f"Transcription error: {str(e)}")
            raise Exception(f"Transcription failed: {str(e)}")