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

# ---------------- INTERVIEW CONFIGURATION ----------------
class InterviewConfig:
    """Configuration for different types of interviews"""
    
    def __init__(self, role_type="marketing", role_title="Marketing Specialist", 
                 company="our company", experience_level="mid-level", 
                 specific_skills=None, interview_focus=None):
        self.role_type = role_type.lower()
        self.role_title = role_title
        self.company = company
        self.experience_level = experience_level
        self.specific_skills = specific_skills or []
        self.interview_focus = interview_focus or []
        
    def get_opening_question(self):
        """Generate role-specific opening question"""
        openings = {
            "marketing": f"Hello! I'm your interviewer today for the {self.role_title} position at {self.company}. Let's begin: Can you introduce yourself and share your experience in marketing, particularly any successful campaigns or strategies you've implemented?",
            
            "social_media": f"Hello! I'm conducting your interview for the {self.role_title} position. To start off: Can you introduce yourself and tell me about your experience managing social media accounts? What platforms have you worked with and what kind of engagement results have you achieved?",
            
            "sales": f"Hello! I'm your interviewer for the {self.role_title} position. Let's begin: Can you introduce yourself and share your sales experience? Tell me about your approach to building client relationships and achieving targets.",
            
            "design": f"Hello! I'm interviewing you for the {self.role_title} position. Let's start: Can you introduce yourself and walk me through your design background? What's your creative process and what design tools do you specialize in?",
            
            "management": f"Hello! I'm conducting your interview for the {self.role_title} position. To begin: Can you introduce yourself and share your leadership experience? How do you approach team management and what's your leadership style?",
            
            "finance": f"Hello! I'm your interviewer for the {self.role_title} position. Let's start: Can you introduce yourself and tell me about your background in finance? What areas of financial analysis or planning have you focused on?",
            
            "hr": f"Hello! I'm interviewing you for the {self.role_title} position. To begin: Can you introduce yourself and share your experience in human resources? What aspects of HR do you find most rewarding?",
            
            "operations": f"Hello! I'm your interviewer for the {self.role_title} position. Let's start: Can you introduce yourself and tell me about your experience in operations? How do you approach process improvement and efficiency?",
            
            "customer_service": f"Hello! I'm conducting your interview for the {self.role_title} position. To begin: Can you introduce yourself and share your customer service experience? How do you handle challenging customer situations?",
            
            "content": f"Hello! I'm your interviewer for the {self.role_title} position. Let's start: Can you introduce yourself and tell me about your content creation experience? What types of content do you enjoy creating most?",
            
            "general": f"Hello! I'm your interviewer today for the {self.role_title} position. Let's start: Can you briefly introduce yourself and tell me about your professional background and what interests you about this role?"
        }
        
        return openings.get(self.role_type, openings["general"])
    
    def get_system_prompt(self):
        """Generate role-specific system prompt for the interviewer"""
        base_prompt = f"You are a professional interviewer conducting an interview for a {self.role_title} position"
        
        if self.company:
            base_prompt += f" at {self.company}"
            
        role_specific_guidance = {
            "marketing": """Focus on marketing strategies, campaign development, market research, brand positioning, digital marketing channels, customer segmentation, ROI measurement, and analytics. 
            Ask about:
            - Successful marketing campaigns they've managed
            - How they measure campaign effectiveness
            - Experience with different marketing channels (email, social, PPC, etc.)
            - Market research and customer insights
            - Budget management and optimization
            - Cross-functional collaboration""",
            
            "social_media": """Focus on social media strategy, content creation, community management, platform-specific knowledge, influencer partnerships, brand voice, and social analytics.
            Ask about:
            - Experience with different social platforms (Instagram, LinkedIn, TikTok, etc.)
            - Content planning and creation process
            - Engagement strategies and community building
            - Social media analytics and KPIs
            - Crisis management on social platforms
            - Influencer collaboration experience""",
            
            "sales": """Focus on sales techniques, lead generation, client relationship building, closing strategies, CRM management, sales targets, negotiation, and customer needs analysis.
            Ask about:
            - Sales methodology and approach
            - Lead generation and qualification
            - Relationship building with prospects
            - Handling objections and closing deals
            - CRM usage and sales process
            - Achieving and exceeding quotas""",
            
            "design": """Focus on design principles, creative process, design software proficiency, user experience, visual communication, brand consistency, and portfolio work.
            Ask about:
            - Design process from concept to completion
            - Software expertise (Adobe Creative Suite, Figma, etc.)
            - Working with brand guidelines
            - Collaborating with non-design stakeholders
            - User research and testing
            - Portfolio pieces and design decisions""",
            
            "management": """Focus on leadership skills, team management, strategic planning, decision-making, performance management, conflict resolution, and organizational development.
            Ask about:
            - Leadership philosophy and style
            - Team building and motivation strategies
            - Performance management and feedback
            - Handling difficult conversations
            - Strategic planning and execution
            - Change management experience""",
            
            "finance": """Focus on financial analysis, budgeting, forecasting, risk assessment, financial reporting, compliance, and business partnership.
            Ask about:
            - Financial modeling and analysis experience
            - Budgeting and forecasting processes
            - Risk management approaches
            - Financial reporting and presentation
            - Business partnering with other departments
            - Regulatory compliance knowledge""",
            
            "hr": """Focus on talent acquisition, employee relations, performance management, HR policies, workplace culture, compensation and benefits, training and development.
            Ask about:
            - Recruiting and hiring processes
            - Employee engagement initiatives
            - Performance review and development
            - HR policy development and implementation
            - Conflict resolution and mediation
            - Training program design and delivery""",
            
            "operations": """Focus on process improvement, project management, supply chain, quality control, efficiency optimization, and cross-functional coordination.
            Ask about:
            - Process analysis and improvement
            - Project management methodologies
            - Quality assurance and control
            - Vendor and supplier management
            - Data analysis for operational decisions
            - Cross-departmental collaboration""",
            
            "customer_service": """Focus on customer relationship management, problem resolution, communication skills, service quality, customer satisfaction, and support processes.
            Ask about:
            - Customer service philosophy
            - Handling difficult customers
            - Problem-solving approaches
            - Customer satisfaction measurement
            - Support tool usage
            - Escalation management""",
            
            "content": """Focus on content strategy, writing and editing, SEO, content management systems, editorial calendars, and audience engagement.
            Ask about:
            - Content creation process
            - SEO and content optimization
            - Editorial calendar management
            - Content performance measurement
            - Writing for different audiences
            - Content management tools""",
            
            "general": "Focus on relevant skills for the position, work experience, problem-solving abilities, communication skills, cultural fit, and motivation for the role."
        }
        
        guidance = role_specific_guidance.get(self.role_type, role_specific_guidance["general"])
        
        if self.specific_skills:
            skills_text = ", ".join(self.specific_skills)
            guidance += f"\n\nPay special attention to these skills: {skills_text}."
            
        if self.interview_focus:
            focus_text = ", ".join(self.interview_focus)
            guidance += f"\n\nFocus areas for this interview: {focus_text}."
        
        return f"""{base_prompt}.

{guidance}

Based on the conversation context and candidate's latest response, provide:
1. Brief evaluation of their answer (2-3 sentences max)
2. Next appropriate question for this {self.role_type} role (concise, clear, and relevant to the position)

Make questions progressively more specific and role-relevant as the interview continues.

Respond in JSON format:
{{"evaluation": "brief feedback here", "next_question": "your next question"}}"""

    def get_nudge_messages(self):
        """Get role-specific nudge messages"""
        role_nudges = {
            "marketing": [
                "I'm still waiting for your response about your marketing experience. Please take your time.",
                "Could you share your thoughts on the marketing question? Feel free to give specific examples.",
                "Take your time to think about a marketing campaign or strategy you'd like to discuss."
            ],
            "social_media": [
                "I'm waiting for your response about social media. Please share your experience when ready.",
                "Could you tell me about your social media work? Examples of campaigns would be great.",
                "Feel free to discuss any social media platforms or strategies you've worked with."
            ],
            "sales": [
                "I'm still waiting to hear about your sales experience. Please take your time.",
                "Could you share your thoughts on the sales question? Specific examples would be helpful.",
                "Take your time to think about a sales situation or achievement you'd like to discuss."
            ],
            "design": [
                "I'm waiting for your response about your design background. Please share when ready.",
                "Could you tell me about your design experience? Portfolio examples would be great.",
                "Feel free to discuss your design process or a project you're proud of."
            ],
            "general": [
                "I'm still waiting for your response. Please take your time to think.",
                "Could you please share your thoughts on the question?",
                "Feel free to think out loud or ask for clarification if needed."
            ]
        }
        
        return role_nudges.get(self.role_type, role_nudges["general"])

# Default interview configuration - can be customized
current_interview_config = InterviewConfig(
    role_type="social_media",
    role_title="Social Media Manager",
    company="our company",
    specific_skills=["Instagram", "Facebook", "LinkedIn", "Content Creation", "Analytics"],
    interview_focus=["Social Strategy", "Community Management", "Content Planning"]
)

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

def interviewer_response(candidate_text: str, conversation_context: list, config: InterviewConfig = None) -> Dict[str, Any]:
    """Generate interviewer response with role-specific context"""
    if config is None:
        config = current_interview_config
        
    # Build context from previous exchanges
    context_str = ""
    if conversation_context:
        recent_context = conversation_context[-3:]  # Last 3 exchanges
        for i, exchange in enumerate(recent_context):
            context_str += f"Q{i+1}: {exchange.get('next_question', exchange.get('question', ''))}\n"
            context_str += f"A{i+1}: {exchange['candidate']}\n\n"

    system_prompt = config.get_system_prompt()
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
                fallback_questions = {
                    "marketing": "Can you tell me about a marketing campaign you're particularly proud of and why it was successful?",
                    "social_media": "Can you describe your approach to creating engaging social media content for different platforms?",
                    "sales": "Can you walk me through your sales process from lead generation to closing?",
                    "design": "Can you describe your design process when working on a new project?",
                    "management": "Can you tell me about a time when you had to lead a team through a challenging situation?",
                    "general": "Can you tell me about your experience with this type of role?"
                }
                return {
                    "evaluation": "Let's continue with the next question.",
                    "next_question": fallback_questions.get(config.role_type, fallback_questions["general"]),
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

def get_user_interview_configuration():
    """Get interview configuration from user input"""
    print("\n🎯 Interview Configuration Setup")
    print("=" * 50)
    
    # Available role types
    available_roles = {
        "1": "marketing",
        "2": "social_media", 
        "3": "sales",
        "4": "design",
        "5": "management",
        "6": "finance",
        "7": "hr",
        "8": "operations",
        "9": "customer_service",
        "10": "content",
        "11": "general"
    }
    
    print("Available role types:")
    for key, role in available_roles.items():
        print(f"{key}. {role.replace('_', ' ').title()}")
    
    # Get role type
    while True:
        try:
            role_choice = input("\nSelect role type (1-11): ").strip()
            if role_choice in available_roles:
                role_type = available_roles[role_choice]
                break
            else:
                print("⚠️ Invalid choice. Please select a number between 1-11.")
        except KeyboardInterrupt:
            print("\n❌ Configuration cancelled.")
            exit(1)
    
    # Get role title
    default_titles = {
        "marketing": "Marketing Specialist",
        "social_media": "Social Media Manager",
        "sales": "Sales Representative", 
        "design": "UX/UI Designer",
        "management": "Team Manager",
        "finance": "Financial Analyst",
        "hr": "HR Coordinator",
        "operations": "Operations Manager",
        "customer_service": "Customer Service Representative",
        "content": "Content Creator",
        "general": "Professional"
    }
    
    default_title = default_titles.get(role_type, "Professional")
    role_title = input(f"Enter role title (default: {default_title}): ").strip()
    if not role_title:
        role_title = default_title
    
    # Get company name
    company = input("Enter company name (default: our company): ").strip()
    if not company:
        company = "our company"
    
    # Get specific skills
    print(f"\nEnter specific skills for {role_type.replace('_', ' ')} role:")
    print("💡 Enter skills separated by commas (e.g., Instagram, LinkedIn, Analytics)")
    skills_input = input("Specific skills: ").strip()
    
    if skills_input:
        specific_skills = [skill.strip() for skill in skills_input.split(',') if skill.strip()]
    else:
        # Default skills based on role type
        default_skills = {
            "marketing": ["Digital Marketing", "Analytics", "Campaign Management", "SEO"],
            "social_media": ["Instagram", "LinkedIn", "Content Creation", "Analytics", "Community Management"],
            "sales": ["CRM", "Lead Generation", "Negotiation", "Presentation"],
            "design": ["Adobe Creative Suite", "Figma", "User Research", "Prototyping"],
            "management": ["Leadership", "Team Building", "Performance Management", "Strategic Planning"],
            "finance": ["Financial Analysis", "Excel", "Budgeting", "Forecasting"],
            "hr": ["Recruitment", "Employee Relations", "HRIS", "Compliance"],
            "operations": ["Process Improvement", "Project Management", "Data Analysis", "Quality Control"],
            "customer_service": ["Communication", "Problem Solving", "CRM", "Conflict Resolution"],
            "content": ["Writing", "Content Strategy", "Social Media", "SEO"],
            "general": ["Communication", "Problem Solving", "Team Work", "Adaptability"]
        }
        specific_skills = default_skills.get(role_type, ["Communication", "Problem Solving"])
    
    # Get interview focus
    print(f"\nEnter interview focus areas for {role_type.replace('_', ' ')} role:")
    print("💡 Enter focus areas separated by commas (e.g., Strategy, Analytics, Team Management)")
    focus_input = input("Interview focus: ").strip()
    
    if focus_input:
        interview_focus = [focus.strip() for focus in focus_input.split(',') if focus.strip()]
    else:
        # Default focus based on role type
        default_focus = {
            "marketing": ["Marketing Strategy", "Campaign Analysis", "Customer Insights"],
            "social_media": ["Social Strategy", "Content Planning", "Engagement Metrics"],
            "sales": ["Sales Process", "Relationship Building", "Closing Techniques"],
            "design": ["Design Process", "User Experience", "Creative Problem Solving"],
            "management": ["Leadership Style", "Team Management", "Decision Making"],
            "finance": ["Financial Analysis", "Budgeting", "Risk Assessment"],
            "hr": ["Talent Acquisition", "Employee Engagement", "HR Policies"],
            "operations": ["Process Optimization", "Quality Management", "Efficiency"],
            "customer_service": ["Customer Relations", "Problem Resolution", "Service Excellence"],
            "content": ["Content Strategy", "Audience Engagement", "Brand Voice"],
            "general": ["Professional Skills", "Experience", "Career Goals"]
        }
        interview_focus = default_focus.get(role_type, ["Professional Experience", "Skills"])
    
    # Display configuration summary
    print(f"\n✅ Interview Configuration Summary:")
    print(f"Role Type: {role_type.replace('_', ' ').title()}")
    print(f"Role Title: {role_title}")
    print(f"Company: {company}")
    print(f"Specific Skills: {', '.join(specific_skills)}")
    print(f"Interview Focus: {', '.join(interview_focus)}")
    
    # Confirm configuration
    confirm = input(f"\nProceed with this configuration? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Configuration cancelled.")
        exit(1)
    
    return role_type, role_title, company, specific_skills, interview_focus

# ---------------- INTERVIEW SESSION ----------------
conversation = []

def start_interview(config: InterviewConfig = None):
    """Give role-specific opening question"""
    if config is None:
        config = current_interview_config
        
    opening = config.get_opening_question()
    print(f"🤖 {config.role_title} Interviewer:", opening)
    play_tts(opening)

def configure_interview(role_type="social_media", role_title="Social Media Manager", 
                       company="our company", specific_skills=None, interview_focus=None):
    """Configure the interview for a specific role"""
    global current_interview_config
    current_interview_config = InterviewConfig(
        role_type=role_type,
        role_title=role_title, 
        company=company,
        specific_skills=specific_skills or [],
        interview_focus=interview_focus or []
    )
    print(f"🔧 Interview configured for: {role_title} ({role_type})")
    if specific_skills:
        print(f"   Focus skills: {', '.join(specific_skills)}")
    if interview_focus:
        print(f"   Focus areas: {', '.join(interview_focus)}")

def run_interview_session(config: InterviewConfig = None):
    """Run the interview session with role-specific configuration"""
    if config is None:
        config = current_interview_config
        
    print(f"🎤 Starting {config.role_title} interview with silence-based detection...")
    print("💡 Speak clearly and pause when finished. Press Ctrl+C to end early.\n")

    start_time = time.time()
    start_interview(config)

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
                        nudge_messages = config.get_nudge_messages()
                        # Cycle through different nudge messages
                        nudge_idx = (round_idx % len(nudge_messages))
                        nudge_msg = nudge_messages[nudge_idx]
                        print(f"🔔 {nudge_msg}")
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
                                        # Generate interviewer response with role-specific context
                                        response_data = interviewer_response(transcript, conversation, config)

                                        # Store conversation
                                        conversation.append({
                                            "round": round_idx,
                                            "candidate": transcript,
                                            "evaluation": response_data.get("evaluation", ""),
                                            "next_question": response_data.get("next_question", ""),
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
    print(f"\n🏁 Generating final feedback for {config.role_title} interview...")
    try:
        role_specific_feedback = f"""
        Interview Summary for {config.role_title} Position:
        Duration: {(time.time() - start_time)/60:.1f} minutes
        Total exchanges: {len(conversation)}

        Conversation history:
        {json.dumps(conversation, indent=2)}

        Please provide comprehensive final feedback for this {config.role_type} interview, including:
        1. Overall performance assessment for the {config.role_title} role
        2. Strengths demonstrated relevant to {config.role_type}
        3. Areas for improvement in {config.role_type} skills
        4. Specific feedback on their responses to {config.role_type}-related questions
        5. Recommendation (hire/no hire/needs more evaluation) for the {config.role_title} position
        """

        system_content = f"You are a senior {config.role_type} interviewer providing final comprehensive feedback for a {config.role_title} position."

        final_feedback = client.chat.completions.create(
            model=LLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": role_specific_feedback}
            ],
            temperature=0.2,
            max_tokens=500,
        )

        feedback_text = final_feedback.choices[0].message.content
        print(f"\n📋 Final {config.role_title} Feedback:\n", feedback_text)
        play_tts(f"Thank you for the {config.role_title} interview. Here is your final feedback: " + feedback_text[:200])

        # Save interview summary
        summary = {
            "role_title": config.role_title,
            "role_type": config.role_type,
            "company": config.company,
            "specific_skills": config.specific_skills,
            "interview_focus": config.interview_focus,
            "duration_minutes": (time.time() - start_time) / 60,
            "total_exchanges": len(conversation),
            "conversation": conversation,
            "final_feedback": feedback_text,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        filename = f"{config.role_type}_interview_summary_{int(time.time())}.json"
        with open(filename, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"\n💾 {config.role_title} interview summary saved to {filename}!")

    except Exception as e:
        print(f"Error generating final feedback: {e}")


if __name__ == "__main__":
    # Check API key
    if not groq_api_key:
        print("❌ Please set GROQ_API_KEY environment variable")
        exit(1)

    print("🎭 General Interview System")
    print("=" * 50)
    
    # Get interview configuration from user input
    role_type, role_title, company, specific_skills, interview_focus = get_user_interview_configuration()
    
    # Configure interview with user input
    configure_interview(
        role_type=role_type,
        role_title=role_title,
        company=company,
        specific_skills=specific_skills,
        interview_focus=interview_focus
    )
    
    print("\n🚀 Starting interview session...")
    run_interview_session()
