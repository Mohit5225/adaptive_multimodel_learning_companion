import os
from dotenv import load_dotenv
from tts_service.audio_generation import AudioGenerationService  # Absolute import

load_dotenv()

# Test your credentials work
service = AudioGenerationService()
audio_file, timestamps = service.generate_audio("""
<speak>
  <mark name="test"/>Dekho yaar, testing Hinglish voice! Samajh aaya?
</speak>
""")

print(f"✅ Audio generated: {audio_file}")
print(f"✅ Timestamps: {timestamps}")