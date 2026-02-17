import os
import json
# Import the specific beta version library for timepoints
from google.cloud import texttospeech_v1beta1 as texttospeech
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GoogleTTSClient:
    def __init__(self):
        # Initialize the client using the beta module
        self.client = texttospeech.TextToSpeechClient()

    def synthesize_ssml(self, ssml_text: str, voice_params: dict, audio_config_params: dict) -> texttospeech.SynthesizeSpeechResponse:
        
        # Instantiate types using the correct module path
        input_text = texttospeech.SynthesisInput(ssml=ssml_text)
        # It takes the 'model_name' key correctly from the incoming 'voice_params' dict
        voice = texttospeech.VoiceSelectionParams(**voice_params) 
        audio_config_params = texttospeech.AudioConfig(**audio_config_params)

        response = self.client.synthesize_speech(
            request={
                "input": input_text,
                "voice": voice,
                "audio_config": audio_config_params,
                # Access TimepointType as an inner class of SynthesizeSpeechRequest
                "enable_time_pointing": [texttospeech.SynthesizeSpeechRequest.TimepointType.SSML_MARK]
            }
        )
        return response
