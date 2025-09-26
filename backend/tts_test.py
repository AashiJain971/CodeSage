import pyttsx3

# engine = pyttsx3.init()
# voices = engine.getProperty('voices')

# for i, voice in enumerate(voices):
#     print(f"Voice {i}: {voice.name} ({voice.id})")
import pyttsx3

engine = pyttsx3.init()

voices = engine.getProperty("voices")

# Choose voice (0 = David, 1 = Zira)
engine.setProperty("voice", voices[1].id)  # Change to voices[0].id for David
engine.setProperty("rate", 120)   # speed (default ~200)
engine.setProperty("volume", 1.0) 
engine.say("Hello, this is a test speech using Microsoft Zira.")
engine.runAndWait()
# range: 0.0 to 1.0


