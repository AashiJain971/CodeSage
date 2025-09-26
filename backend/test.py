import os
import time
import json
import queue
import numpy as np
import sounddevice as sd
import soundfile as sf
from pathlib import Path
from groq import Groq
import webrtcvad
import threading
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import pyttsx3

# Load env
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=groq_api_key)

# Initialize pyttsx3 TTS engine as fallback
try:
    fallback_tts_engine = pyttsx3.init()
    voices = fallback_tts_engine.getProperty("voices")
    if voices:
        fallback_tts_engine.setProperty("voice", voices[1].id if len(voices) > 1 else voices[0].id)
    fallback_tts_engine.setProperty("rate", 120)
    fallback_tts_engine.setProperty("volume", 1.0)
except Exception as e:
    print(f"Warning: Could not initialize fallback TTS engine: {e}")
    fallback_tts_engine = None

# Models / config
WHISPER_MODEL = "whisper-large-v3-turbo"
LLAMA_MODEL = "llama-3.3-70b-versatile"
TTS_MODEL = "playai-tts"
VOICE = "Aaliyah-PlayAI"

SAMPLE_RATE = 16000
CHANNELS = 1
FRAME_DURATION_MS = 20   # 20ms per frame for VAD
SESSION_MINUTES = 10
SILENCE_THRESHOLD_SEC = 1  # how long silence before we cut segment
MIN_SPEECH_DURATION = 0.8  # minimum speech duration to process (seconds)
MAX_SILENCE_GAP = 3.0       # max silence before prompting candidate

# ---------------- TECHNICAL INTERVIEW CATEGORIES ----------------
TECHNICAL_CATEGORIES = {
    "dbms": "Database Management Systems (SQL, NoSQL, Database Design, Transactions, Indexing)",
    "oops": "Object-Oriented Programming (Classes, Inheritance, Polymorphism, Encapsulation, Design Patterns)",
    "system_design": "System Design (Scalability, Load Balancing, Microservices, Distributed Systems, Architecture)",
    "dsa": "Data Structures and Algorithms (Arrays, Trees, Graphs, Sorting, Dynamic Programming, Complexity Analysis)",
    "design": "Software Design (Design Patterns, Architecture, Code Quality, SOLID Principles)"
}

# Global variable to store selected categories
selected_categories = []

def select_interview_categories():
    """Allow user to select one or more technical categories"""
    global selected_categories
    
    print("\n🎯 Technical Interview Category Selection")
    print("=" * 50)
    print("Available categories:")
    
    for i, (key, description) in enumerate(TECHNICAL_CATEGORIES.items(), 1):
        print(f"{i}. {key.upper()}: {description}")
    
    print("\n💡 Instructions:")
    print("- Enter category numbers separated by commas (e.g., 1,3,4)")
    print("- Or press Enter for all categories")
    
    try:
        user_input = input("\nSelect categories (1-5): ").strip()
        
        if not user_input:
            # If no input, select all categories
            selected_categories = list(TECHNICAL_CATEGORIES.keys())
        else:
            # Parse user selection
            numbers = [int(x.strip()) for x in user_input.split(',')]
            category_list = list(TECHNICAL_CATEGORIES.keys())
            selected_categories = [category_list[i-1] for i in numbers if 1 <= i <= len(category_list)]
        
        if not selected_categories:
            print("⚠️ No valid categories selected. Using all categories.")
            selected_categories = list(TECHNICAL_CATEGORIES.keys())
            
        print(f"\n✅ Selected categories: {[cat.upper() for cat in selected_categories]}")
        return selected_categories
        
    except (ValueError, IndexError) as e:
        print(f"⚠️ Invalid input. Using all categories.")
        selected_categories = list(TECHNICAL_CATEGORIES.keys())
        return selected_categories

# ---------------- AUDIO HELPERS ----------------
vad = webrtcvad.Vad(2)  # 0=less sensitive, 3=most sensitive
audio_queue = queue.Queue()
is_playing_tts = threading.Event()

def audio_callback(indata, frames, time_, status):
    if status:
        print(f"Audio status: {status}")
    # Only capture audio when not playing TTS to avoid feedback
    if not is_playing_tts.is_set():
        # indata is shape (frames, channels)
        audio_queue.put(indata.copy())

def frame_generator(frame_duration_ms, audio, sample_rate):
    """Yield contiguous frames of `n` samples (1-D numpy array)."""
    n = int(sample_rate * (frame_duration_ms / 1000.0))
    offset = 0
    # audio is a 1-D numpy array of samples
    while offset + n <= len(audio):
        yield audio[offset:offset + n]
        offset += n

def save_wav(filename: str, data: np.ndarray, samplerate: int = SAMPLE_RATE) -> bool:
    """Save a 1-D numpy array (int16 or float) to WAV with error handling."""
    try:
        if data is None or len(data) == 0:
            print("save_wav: no data to write")
            return False
        # If data is float in [-1,1], write as float; if int16, write as int16
        sf.write(filename, data, samplerate)
        return True
    except Exception as e:
        print(f"Error saving audio to {filename}: {e}")
    return False

def estimate_audio_duration(samples: np.ndarray, sample_rate: int = SAMPLE_RATE) -> float:
    """Estimate audio duration in seconds from 1-D samples array."""
    if samples is None or len(samples) == 0:
        return 0.0
    return float(len(samples)) / float(sample_rate)

# ---------------- API HELPERS ----------------
def transcribe_audio(filename: str) -> Optional[str]:
    """Transcribe audio with error handling and retry"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            with open(filename, "rb") as f:
                # Groq client expects file bytes; this pattern matched your earlier usage
                result = client.audio.transcriptions.create(
                    file=(filename, f.read()),
                    model=WHISPER_MODEL,
                    response_format="verbose_json",
                )
            # result.text should hold the transcript
            text = getattr(result, "text", None)
            if text:
                text = text.strip()
                # Filter out common Whisper hallucinations from silence/noise
                hallucinations = {"thank you", "thanks", "thank you.", "thanks.", "thank you very much", 
                                "you", ".", "", " ", "um", "uh", "hmm", "mhm", "mm-hmm"}
                if text.lower() in hallucinations or len(text) < 3:
                    return None
                return text if text else None
            return None
        except Exception as e:
            print(f"Transcription error (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                return None
            time.sleep(1)

def interviewer_response(candidate_text: str, conversation_context: list) -> Dict[str, Any]:
    """Generate interviewer response with better context"""
    # Build context from previous exchanges
    context_str = ""
    if conversation_context:
        recent_context = conversation_context[-3:]  # Last 3 exchanges
        for i, exchange in enumerate(recent_context):
            context_str += f"Q{i+1}: {exchange.get('question', '')}\n"
            context_str += f"A{i+1}: {exchange['candidate']}\n\n"

    # Build technical focus areas from selected categories
    focus_areas = []
    for category in selected_categories:
        focus_areas.append(TECHNICAL_CATEGORIES[category])
    
    focus_text = "\n".join([f"- {area}" for area in focus_areas])

    system_prompt = (
        f"You are a professional technical interviewer conducting a coding/technical interview.\n"
        f"Focus on these technical areas:\n{focus_text}\n\n"
        f"Based on the conversation context and candidate's latest response, provide:\n"
        "1. Brief evaluation of their answer (2-3 sentences max)\n"
        "2. Next appropriate technical question from the focus areas (concise, clear)\n\n"
        "Respond in JSON format:\n"
        '{\n  "evaluation": "brief feedback here",\n'
        '  "next_question": "your next question"\n}'
    )

    prompt = f"Context:\n{context_str}\nLatest candidate response: {candidate_text}"

    max_retries = 2
    for attempt in range(max_retries):
        try:
            chat_completion = client.chat.completions.create(
                model=LLAMA_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=300,
            )
            response = chat_completion.choices[0].message.content

            # Try to parse JSON
            try:
                parsed = json.loads(response)
                return {
                    "evaluation": parsed.get("evaluation", ""),
                    "next_question": parsed.get("next_question", ""),
                    "raw_response": response
                }
            except json.JSONDecodeError:
                # Fallback: treat as plain text (LLM might not return strict JSON)
                return {
                    "evaluation": "Response received",
                    "next_question": response,
                    "raw_response": response
                }
        except Exception as e:
            print(f"LLM error (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                return {
                    "evaluation": "Let's continue with the next question.",
                    "next_question": "Can you tell me about your experience with this topic?",
                    "raw_response": ""
                }
            time.sleep(1)

def play_tts(text: str, out_path: Path = Path("interviewer.wav")) -> bool:
    """Play TTS with Groq client: save binary response to file then play it. Fallback to pyttsx3 on failure."""
    if not text or not text.strip():
        return False

    try:
        is_playing_tts.set()  # Signal that TTS is playing

        response = client.audio.speech.create(
            model=TTS_MODEL,
            voice=VOICE,
            response_format="wav",  # returns binary wav
            input=text[:500],  # Limit length to avoid timeout
        )

        # Write binary content to out_path
        with open(out_path, "wb") as f:
            f.write(response.read())

        # Read and play
        data, sr = sf.read(str(out_path), dtype="float32")
        sd.play(data, sr)
        sd.wait()
        return True
    except Exception as e:
        print(f"PlayAI TTS error: {e}")
        print("Using fallback TTS...")
        
        # Fallback to pyttsx3
        if fallback_tts_engine is not None:
            try:
                fallback_tts_engine.say(text[:500])  # Limit length
                fallback_tts_engine.runAndWait()
                return True
            except Exception as fallback_error:
                print(f"Fallback TTS error: {fallback_error}")
        else:
            print("Fallback TTS not available")
        
        return False
    finally:
        is_playing_tts.clear()  # Clear the flag

# ---------------- INTERVIEW SESSION ----------------
conversation = []

def start_interview():
    """Give opening question"""
    categories_text = ", ".join([cat.upper() for cat in selected_categories])
    opening = (f"Hello! I'm your technical interviewer today. We'll be focusing on {categories_text}. "
               f"Let's start with a simple question: "
               f"Can you briefly introduce yourself and tell me about your programming background?")
    print("🤖 Interviewer:", opening)
    play_tts(opening)

def run_interview_session():
    print("🎤 Starting 20-minute mock interview with silence-based detection...")
    print("💡 Speak clearly and pause when finished. Press Ctrl+C to end early.\n")

    start_time = time.time()
    start_interview()

    # buffer will be a list of 1-D numpy arrays (frames). We'll concatenate when utterance ends.
    buffer = []
    speech_active = False
    silence_start = None
    speech_start = None
    round_idx = 0
    last_prompt_time = time.time()

    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            callback=audio_callback,
            blocksize=int(SAMPLE_RATE * FRAME_DURATION_MS / 1000),
        ):
            while (time.time() - start_time) < SESSION_MINUTES * 60:
                try:
                    # Get audio chunk with timeout
                    audio_chunk = audio_queue.get(timeout=0.1)
                    # audio_chunk shape: (frames, channels). Convert to mono 1-D array
                    if CHANNELS > 1:
                        audio_chunk = np.mean(audio_chunk, axis=1)
                    else:
                        audio_chunk = audio_chunk.flatten()
                except queue.Empty:
                    # Check if candidate has been silent too long
                    if not speech_active and (time.time() - last_prompt_time) > MAX_SILENCE_GAP:
                        nudge_messages = [
                            "I'm still waiting for your response. Please take your time.",
                            "Could you please share your thoughts on the question?",
                            "Feel free to think out loud or ask for clarification if needed."
                        ]
                        # Cycle through different nudge messages
                        nudge_idx = (round_idx % len(nudge_messages))
                        nudge_msg = nudge_messages[nudge_idx]
                        print(f"{nudge_msg}")
                        play_tts(nudge_msg)
                        last_prompt_time = time.time()
                    continue

                # Process audio frames for VAD (we split the received chunk into frame-sized pieces)
                for frame in frame_generator(FRAME_DURATION_MS, audio_chunk, SAMPLE_RATE):
                    if len(frame) < int(SAMPLE_RATE * FRAME_DURATION_MS / 1000):
                        continue

                    # webrtcvad expects 16-bit little-endian PCM bytes
                    pcm_bytes = frame.tobytes()
                    try:
                        is_speech_frame = vad.is_speech(pcm_bytes, SAMPLE_RATE)
                    except Exception as e:
                        # If VAD fails, assume silence to avoid infinite listening
                        print(f"VAD error: {e}")
                        is_speech_frame = False

                    if is_speech_frame:
                        if not speech_active:
                            speech_start = time.time()
                            print("🎙  Listening...")
                        # keep raw int16 samples
                        # ensure frame dtype is int16
                        frame_int16 = frame.astype(np.int16)
                        buffer.append(frame_int16)
                        speech_active = True
                        silence_start = None
                    elif speech_active:
                        # add the silent frame as well (to avoid chopping off the end)
                        frame_int16 = frame.astype(np.int16)
                        buffer.append(frame_int16)

                        if silence_start is None:
                            silence_start = time.time()
                        elif (time.time() - silence_start) > SILENCE_THRESHOLD_SEC:
                            # End of utterance - concatenate and check duration
                            samples = np.concatenate(buffer) if buffer else np.array([], dtype=np.int16)
                            speech_duration = estimate_audio_duration(samples, SAMPLE_RATE)

                            if speech_duration >= MIN_SPEECH_DURATION:
                                round_idx += 1
                                filename = f"candidate_{round_idx}.wav"

                                if save_wav(filename, samples, SAMPLE_RATE):
                                    print(f"\n⏸  Processing response {round_idx} ({speech_duration:.1f}s)...")

                                    # Transcribe
                                    transcript = transcribe_audio(filename)

                                    if transcript:
                                        # Generate interviewer response
                                        response_data = interviewer_response(transcript, conversation)

                                        # Store conversation
                                        conversation.append({
                                            "question": round_idx,
                                            "candidate": transcript,
                                            "evaluation": response_data.get("evaluation", ""),
                                            "question": response_data.get("next_question", ""),
                                            "feedback": response_data.get("raw_response", ""),
                                            "timestamp": time.time() - start_time
                                        })


                                        # Ask next question
                                        if response_data.get("next_question"):
                                            print(f" Next question: {response_data['next_question']}")
                                            play_tts(response_data["next_question"])
                                            last_prompt_time = time.time()
                                    else:
                                        # Provide helpful feedback when transcription fails
                                        retry_msg = "I couldn't hear that clearly. Could you please repeat your answer or speak a bit louder?"
                                        print(f"{retry_msg}")
                                        play_tts(retry_msg)
                                        last_prompt_time = time.time()

                                    # Clean up saved file
                                    try:
                                        os.remove(filename)
                                    except Exception:
                                        pass

                            # Reset for next utterance
                            buffer = []
                            speech_active = False
                            silence_start = None

    except KeyboardInterrupt:
        print("\n Interview ended early by user")
    except Exception as e:
        print(f"\n Unexpected error: {e}")

    # Generate final feedback
    print("\nenerating final feedback...")
    try:
        final_prompt = f"""
        Interview Summary:
        Duration: {(time.time() - start_time)/60:.1f} minutes
        Total exchanges: {len(conversation)}

        Conversation history:
        {json.dumps(conversation, indent=2)}

        Please provide comprehensive final feedback for this technical interview, including:
        1. Overall performance assessment
        2. Strengths demonstrated
        3. Areas for improvement
        4. Recommendation (hire/no hire/needs more evaluation)
        """

        final_feedback = client.chat.completions.create(
            model=LLAMA_MODEL,
            messages=[
                {"role": "system", "content": "You are a senior technical interviewer providing final comprehensive feedback."},
                {"role": "user", "content": final_prompt}
            ],
            temperature=0.2,
            max_tokens=500,
        )

        feedback_text = final_feedback.choices[0].message.content
        print("\nFinal Feedback:\n", feedback_text)
        play_tts("Thank you for the interview. Here is your final feedback: " )

        # Save interview summary
        summary = {
            "duration_minutes": (time.time() - start_time) / 60,
            "total_exchanges": len(conversation),
            "conversation": conversation,
            "final_feedback": feedback_text,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        with open(f"interview_summary_{int(time.time())}.json", "w") as f:
            json.dump(summary, f, indent=2)
        print("\n💾 Interview summary saved!")

    except Exception as e:
        print(f"Error generating final feedback: {e}")


if __name__ == "__main__":
    # Check API key
    if not groq_api_key:
        print("Please set GROQ_API_KEY environment variable")
        exit(1)

    # Select interview categories
    select_interview_categories()
    
    run_interview_session()
