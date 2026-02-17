import os
from pathlib import Path
from .google_tts_client import GoogleTTSClient
from typing import Tuple, List
from google.cloud import texttospeech

class AudioGenerationService:
    def __init__(self):
        self.tts_client = GoogleTTSClient()

    def generate_audio(
        self, 
        ssml_script: str, 
        output_dir: str = "output_audio",
        voice_params: dict = None,
        audio_config_params: dict = None
    ) -> Tuple[str, List[dict]]:
        """
        Input:
            ssml_script: full SSML text including <mark> tags for beats
            output_dir: directory to save audio file
            voice_params: dict of voice selection options (lang_code, name, ssml_gender, model_name)
            audio_config: dict for audio settings (mp3, rate, pitch, volume)
        Returns:
            - Path to saved audio file (wav or mp3)
            - List of timepoints with {'mark_name': str, 'time_seconds': float}
        """

        if voice_params is None:
            voice_params = {
                "language_code": "hi-IN", # Updated to Hindi (India)
                "name": "Aoede",          # Specified voice name
                "model_name": "gemini-2.5-flash-tts", # Specified model name
                "prompt": "Read aloud in a warm, welcoming tone.",
            }

        if audio_config_params is None:
            audio_config_params = {
                "audio_encoding": texttospeech.AudioEncoding.MP3,
                "speaking_rate": 1.0,
                "pitch": 0.4,
            }

        response = self.tts_client.synthesize_ssml(
            ssml_text=ssml_script,
            voice_params=voice_params,
            audio_config_params=audio_config_params
        )

        Path(output_dir).mkdir(exist_ok=True)
        output_audio_file = os.path.join(output_dir, "lesson_audio.mp3")

        with open(output_audio_file, "wb") as out:
            out.write(response.audio_content)

        # Extract timepoints: convert protobuf to simple dicts
        timepoints = []
        if hasattr(response, "timepoints"):
            for tp in response.timepoints:
                timepoints.append({
                    "mark_name": tp.mark_name,
                    "time_seconds": tp.time_seconds,
                })

        return output_audio_file, timepoints
