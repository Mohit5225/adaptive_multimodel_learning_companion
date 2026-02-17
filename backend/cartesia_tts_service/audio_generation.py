import os
import wave
import numpy as np
from pathlib import Path
from .cartesia_tts_client import CartesiaTTSClient
from typing import Tuple, List
from dotenv import load_dotenv

load_dotenv()

class AudioGenerationService:
    def __init__(self):
        """Initialize Cartesia TTS service."""
        self.tts_client = CartesiaTTSClient()

    def generate_audio(
        self, 
        transcript: str,  # Plain text (no SSML needed for Cartesia)
        output_dir: str = "output_audio",
        voice_params: dict = None,
        audio_config_params: dict = None,
        use_timestamps: bool = True
    ) -> Tuple[str, List[dict]]:
        """
        Generate audio with word-level timestamps using Cartesia TTS.
        
        Input:
            transcript: Plain text to synthesize
            output_dir: directory to save audio file
            voice_params: dict with voice selection (e.g., {"mode": "id", "id": "voice-uuid"})
            audio_config_params: dict for audio settings (container, sample_rate)
            use_timestamps: whether to extract timestamps (default True)
        
        Returns:
            - Tuple of (audio_file_path, timepoints_list)
            - timepoints_list: List of dicts with {'word': str, 'time_seconds': float, 'duration': float}
        
        Supported Languages (with timestamps):
            - English (en)
            - German (de)
            - Spanish (es)
            - French (fr)
        """

        # ═══════════════════════════════════════════════════════════════════
        # Default voice parameters
        # ═══════════════════════════════════════════════════════════════════
        if voice_params is None:
            voice_params = {
                "mode": "id",
                "id": "6ccbfb76-1fc6-48f7-b71d-91ac6298247b",  # Sarah (English voice)
               
            }

        if audio_config_params is None:
            audio_config_params = {
                "container": "mp3",      # "mp3" or "wav"
                "sample_rate": 22050,    # Supported: 8000, 16000, 22050, 24000, 44100, 48000
                "encoding": "pcm_s16le",
                 "speed": 0.9 
            }

        # ═══════════════════════════════════════════════════════════════════
        # Generate audio with timestamps
        # ═══════════════════════════════════════════════════════════════════
        try:
            print(f"🎤 Generating audio with Cartesia TTS...")
            print(f"   📝 Transcript length: {len(transcript)} characters")
            print(f"   🎵 Sample rate: {audio_config_params['sample_rate']}Hz")
            print(f"   📦 Container: {audio_config_params['container']}")
            print(f"   ⏱️  Timestamps enabled: {use_timestamps}")

            if use_timestamps:
                # Use WebSocket for timestamps
                audio_bytes, timepoints = self.tts_client.synthesize_with_timestamps(
                    transcript=transcript,
                    voice_params=voice_params,
                    audio_config_params=audio_config_params
                )
            else:
                # Use simple bytes endpoint
                audio_bytes = self.tts_client.synthesize_bytes_only(
                    transcript=transcript,
                    voice_params=voice_params,
                    audio_config_params=audio_config_params
                )
                timepoints = []

            # ═══════════════════════════════════════════════════════════════════
            # Save audio to file
            # ═══════════════════════════════════════════════════════════════════
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Handle raw PCM data from SSE/WebSocket (when timestamps are enabled)
            if use_timestamps:
                # Cartesia returns raw pcm_f32le when timestamps are requested
                # We need to convert this to a standard WAV file for compatibility
                print("⚠️  Converting raw PCM (float32) to WAV (int16)...")
                
                # Convert bytes to float32 numpy array
                audio_data = np.frombuffer(audio_bytes, dtype=np.float32)
                
                # Convert float32 [-1.0, 1.0] to int16 [-32768, 32767]
                audio_data_int16 = (audio_data * 32767).astype(np.int16)
                
                file_extension = "wav"
                output_audio_file = os.path.join(output_dir, f"lesson_audio.{file_extension}")
                
                sample_rate = int(audio_config_params.get("sample_rate", 44100))
                
                with wave.open(output_audio_file, "wb") as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(audio_data_int16.tobytes())
            else:
                # Standard container (mp3/wav)
                file_extension = audio_config_params.get("container", "mp3")
                output_audio_file = os.path.join(output_dir, f"lesson_audio.{file_extension}")

                with open(output_audio_file, "wb") as out:
                    out.write(audio_bytes)

            print(f"✅ Audio saved: {output_audio_file}")
            print(f"   📊 File size: {len(audio_bytes) / 1024:.1f} KB")
            print(f"   ⏱️  Timepoints extracted: {len(timepoints)}")

            if timepoints:
                print(f"   📍 First 3 timepoints:")
                for tp in timepoints[:3]:
                    print(f"      - '{tp['word']}' @ {tp['time_seconds']:.2f}s (duration: {tp['duration']:.2f}s)")

            return output_audio_file, timepoints

        except Exception as e:
            print(f"❌ Error generating audio: {e}")
            raise

    def batch_generate_audio(
        self,
        transcripts: List[str],
        output_dir: str = "output_audio",
        voice_params: dict = None,
        audio_config_params: dict = None
    ) -> List[Tuple[str, List[dict]]]:
        """
        Generate multiple audio files in sequence.
        
        Args:
            transcripts: List of text strings to synthesize
            output_dir: directory to save all audio files
            voice_params: shared voice parameters
            audio_config_params: shared audio config
        
        Returns:
            List of (audio_file_path, timepoints) tuples
        """
        results = []
        for i, transcript in enumerate(transcripts):
            print(f"\n🔄 Processing transcript {i+1}/{len(transcripts)}...")
            
            output_subdir = os.path.join(output_dir, f"batch_{i}")
            audio_path, timepoints = self.generate_audio(
                transcript=transcript,
                output_dir=output_subdir,
                voice_params=voice_params,
                audio_config_params=audio_config_params
            )
            results.append((audio_path, timepoints))
        
        return results