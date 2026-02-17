from dotenv import load_dotenv
import google.cloud.texttospeech as tts
load_dotenv()

def list_voices(language_code):
    client = tts.TextToSpeechClient()
    response = client.list_voices(language_code=language_code)
    voices = sorted(response.voices, key=lambda voice: voice.name)

    print(f"--- Available Voices for {language_code} ---")
    for voice in voices:
        languages = ", ".join(voice.language_codes)
        name = voice.name
        gender = tts.SsmlVoiceGender(voice.ssml_gender).name
        rate = voice.natural_sample_rate_hertz
        print(f"Language: {languages} | Name: {name} | Gender: {gender} | Sample Rate: {rate} Hz")

# Call this function to see your available options
list_voices(language_code="hi-IN")
