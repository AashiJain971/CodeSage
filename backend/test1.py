

from TTS.api import TTS

# Load English VITS model
tts = TTS("tts_models/en/ljspeech/vits", gpu=False)

# Run test
tts.tts_to_file(
    text="Hello, I am your interview agent. Let's start with a few questions about your background.",
    file_path="test_vits_en.wav"
)
print("Generated: test_vits_en.wav")



