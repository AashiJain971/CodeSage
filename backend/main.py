from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
import threading
import time
from typing import Optional, Dict, Any
import uvicorn

# Import your existing interview logic
from test import (
    run_interview_session, conversation, groq_api_key, client,
    start_interview, play_tts, interviewer_response,
    transcribe_audio, save_wav, estimate_audio_duration,
    vad, audio_queue, is_playing_tts, frame_generator,
    SAMPLE_RATE, CHANNELS, FRAME_DURATION_MS, SESSION_MINUTES,
    SILENCE_THRESHOLD_SEC, MIN_SPEECH_DURATION, MAX_SILENCE_GAP,
    TECHNICAL_CATEGORIES, selected_categories, select_interview_categories,
    fallback_tts_engine, TTS_MODEL, VOICE
)
import sounddevice as sd
import soundfile as sf
import numpy as np
import queue
import os
from pathlib import Path
import pyttsx3

app = FastAPI(title="AI Interview System", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state management
active_interviews: Dict[str, Dict] = {}
interview_lock = threading.Lock()
message_queues: Dict[str, queue.Queue] = {}

# ---------------- INTERVIEW CONFIGURATION ----------------
class InterviewConfig(BaseModel):
    role_type: Optional[str] = "technical"
    role_title: Optional[str] = "Technical Specialist"
    company: Optional[str] = "our company"
    session_minutes: Optional[int] = 10
    candidate_name: Optional[str] = "Candidate"
    interview_type: Optional[str] = "technical"
    specific_skills: Optional[list] = []
    interview_focus: Optional[list] = []
    technical_categories: Optional[list] = []  # For technical interviews

    def get_opening_question(self):
        """Generate role-specific opening question"""
        if self.interview_type == "technical":
            if self.technical_categories:
                categories_text = ", ".join([cat.upper() for cat in self.technical_categories])
                return (f"Hello! I'm your technical interviewer today. We'll be focusing on {categories_text}. "
                       f"Let's start with a simple question: "
                       f"Can you briefly introduce yourself and tell me about your programming background?")
            else:
                return ("Hello! I'm your technical interviewer today. Let's start with a simple question: "
                       "Can you briefly introduce yourself and tell me about your programming background?")
        else:
            # Role-based openings
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

class TechnicalInterviewConfig(BaseModel):
    session_minutes: Optional[int] = 10
    candidate_name: Optional[str] = "Candidate"
    interview_type: str = "technical"
    technical_categories: Optional[list] = []

class RoleBasedInterviewConfig(BaseModel):
    role_type: str
    role_title: Optional[str] = None
    company: Optional[str] = "our company"
    session_minutes: Optional[int] = 10
    candidate_name: Optional[str] = "Candidate"
    interview_type: str = "role_based"
    specific_skills: Optional[list] = []
    interview_focus: Optional[list] = []

class InterviewResponse(BaseModel):
    status: str
    message: str
    interview_id: Optional[str] = None
    data: Optional[Dict] = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AI Interview System is running", "status": "active"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "api_key_configured": bool(groq_api_key),
        "active_interviews": len(active_interviews)
    }

@app.post("/interview/start", response_model=InterviewResponse)
async def start_new_interview(config: InterviewConfig):
    """Start a new interview session"""
    if not groq_api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")
    
    interview_id = f"interview_{int(time.time())}"
    
    with interview_lock:
        active_interviews[interview_id] = {
            "status": "started",
            "config": config.dict(),
            "start_time": time.time(),
            "conversation": [],
            "websocket": None
        }
        message_queues[interview_id] = queue.Queue()
    
    return InterviewResponse(
        status="success",
        message="Interview session created",
        interview_id=interview_id,
        data={"config": config.dict()}
    )

@app.post("/interview/technical/start", response_model=InterviewResponse)
async def start_technical_interview(config: TechnicalInterviewConfig):
    """Start a new technical interview with category selection"""
    if not groq_api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")
    
    interview_id = f"interview_{int(time.time())}"
    
    # Validate technical categories
    if config.technical_categories:
        valid_categories = set(TECHNICAL_CATEGORIES.keys())
        invalid_categories = set(config.technical_categories) - valid_categories
        if invalid_categories:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid technical categories: {list(invalid_categories)}. Valid options: {list(valid_categories)}"
            )
    
    with interview_lock:
        active_interviews[interview_id] = {
            "status": "started",
            "config": config.dict(),
            "start_time": time.time(),
            "conversation": [],
            "websocket": None,
            "technical_categories": config.technical_categories or list(TECHNICAL_CATEGORIES.keys())
        }
        message_queues[interview_id] = queue.Queue()
    
    return InterviewResponse(
        status="success",
        message="Technical interview session created",
        interview_id=interview_id,
        data={
            "config": config.dict(),
            "available_categories": TECHNICAL_CATEGORIES,
            "selected_categories": config.technical_categories or list(TECHNICAL_CATEGORIES.keys())
        }
    )

@app.post("/interview/role-based/start", response_model=InterviewResponse)
async def start_role_based_interview(config: RoleBasedInterviewConfig):
    """Start a new role-based interview"""
    if not groq_api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")
    
    interview_id = f"interview_{int(time.time())}"
    
    # Set default role title if not provided
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
    
    if not config.role_title:
        config.role_title = default_titles.get(config.role_type, "Professional")
    
    with interview_lock:
        active_interviews[interview_id] = {
            "status": "started",
            "config": config.dict(),
            "start_time": time.time(),
            "conversation": [],
            "websocket": None
        }
        message_queues[interview_id] = queue.Queue()
    
    return InterviewResponse(
        status="success",
        message="Role-based interview session created",
        interview_id=interview_id,
        data={"config": config.dict()}
    )

@app.get("/interview/categories")
async def get_technical_categories():
    """Get available technical categories"""
    return {
        "categories": TECHNICAL_CATEGORIES,
        "description": "Available technical interview categories"
    }

@app.get("/interview/roles")
async def get_available_roles():
    """Get available role types for role-based interviews"""
    roles = {
        "marketing": "Marketing roles focusing on campaigns, strategy, and customer acquisition",
        "social_media": "Social media management and content strategy roles",
        "sales": "Sales and business development positions",
        "design": "UX/UI and creative design roles",
        "management": "Leadership and team management positions",
        "finance": "Financial analysis and planning roles",
        "hr": "Human resources and talent management",
        "operations": "Operations and process management",
        "customer_service": "Customer support and service roles",
        "content": "Content creation and marketing roles",
        "general": "General professional interviews"
    }
    
    return {
        "roles": roles,
        "description": "Available role types for role-based interviews"
    }

@app.get("/interview/{interview_id}/status")
async def get_interview_status(interview_id: str):
    """Get the status of a specific interview"""
    if interview_id not in active_interviews:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    interview = active_interviews[interview_id]
    elapsed_time = time.time() - interview["start_time"]
    
    return {
        "interview_id": interview_id,
        "status": interview["status"],
        "elapsed_minutes": elapsed_time / 60,
        "total_exchanges": len(interview["conversation"]),
        "remaining_minutes": max(0, interview["config"]["session_minutes"] - elapsed_time / 60)
    }

@app.delete("/interview/{interview_id}")
async def end_interview(interview_id: str):
    """End a specific interview session"""
    if interview_id not in active_interviews:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    with interview_lock:
        interview = active_interviews[interview_id]
        interview["status"] = "ended"
        
        # Generate final summary
        summary = generate_interview_summary(interview)
        
        # Save summary to file
        filename = f"interview_summary_{interview_id}.json"
        with open(filename, "w") as f:
            json.dump(summary, f, indent=2)
        
        # Clean up
        del active_interviews[interview_id]
        if interview_id in message_queues:
            del message_queues[interview_id]
    
    return InterviewResponse(
        status="success",
        message="Interview ended successfully",
        data={"summary_file": filename}
    )

@app.websocket("/interview/{interview_id}/connect")
async def interview_websocket(websocket: WebSocket, interview_id: str):
    """WebSocket endpoint for real-time interview communication"""
    if interview_id not in active_interviews:
        await websocket.close(code=4004, reason="Interview not found")
        return
    
    await websocket.accept()
    
    with interview_lock:
        active_interviews[interview_id]["websocket"] = websocket
        active_interviews[interview_id]["status"] = "active"
    
    try:
        # Start the interview logic in a separate thread
        interview_thread = threading.Thread(
            target=run_websocket_interview,
            args=(websocket, interview_id),
            daemon=True
        )
        interview_thread.start()
        
        # Keep the connection alive and handle incoming messages
        while True:
            try:
                # Check for messages from the interview thread
                if interview_id in message_queues:
                    try:
                        message = message_queues[interview_id].get_nowait()
                        await websocket.send_json(message)
                    except queue.Empty:
                        pass
                
                # Handle client messages
                try:
                    data = await asyncio.wait_for(websocket.receive_json(), timeout=0.1)
                    await handle_websocket_message(websocket, interview_id, data)
                except asyncio.TimeoutError:
                    # No message received, continue loop
                    pass
                    
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for interview {interview_id}")
    except Exception as e:
        print(f"WebSocket error for interview {interview_id}: {e}")
        await websocket.close(code=4000, reason=f"Server error: {str(e)}")
    finally:
        # Clean up
        with interview_lock:
            if interview_id in active_interviews:
                active_interviews[interview_id]["status"] = "disconnected"
                active_interviews[interview_id]["websocket"] = None
            if interview_id in message_queues:
                del message_queues[interview_id]

async def handle_websocket_message(websocket: WebSocket, interview_id: str, data: Dict):
    """Handle messages received from the WebSocket client"""
    message_type = data.get("type")
    
    if message_type == "ping":
        await websocket.send_json({"type": "pong", "timestamp": time.time()})
    elif message_type == "end_interview":
        await websocket.send_json({"type": "interview_ending", "message": "Ending interview..."})
        # The interview thread will handle the actual ending
    elif message_type == "audio_data":
        # Handle audio data if sent from client
        # This would require additional implementation for web audio
        pass

def run_websocket_interview(websocket, interview_id: str):
    """Run the interview logic with WebSocket communication"""
    interview = active_interviews.get(interview_id)
    if not interview:
        return
    
    config = interview["config"]
    session_minutes = config["session_minutes"]
    start_time = time.time()
    
    # Send initial message
    queue_websocket_message(
        interview_id, 
        "interview_started", 
        {"message": "Interview session started", "duration_minutes": session_minutes}
    )
    
    # Generate opening question based on interview type
    interview_config = InterviewConfig(**config)
    if hasattr(interview, 'technical_categories'):
        interview_config.technical_categories = interview['technical_categories']
    
    opening = interview_config.get_opening_question()
    
    queue_websocket_message(
        interview_id,
        "interviewer_question",
        {"message": opening, "round": 0}
    )
    
    # Play the opening TTS
    play_tts_websocket(opening, interview_id)
    
    # Use your existing interview logic with WebSocket integration
    run_interview_with_websocket(websocket, interview_id, session_minutes, start_time)

def interviewer_response_websocket(candidate_text: str, conversation_context: list, interview_id: str) -> Dict[str, Any]:
    """Generate interviewer response based on interview type and configuration"""
    interview = active_interviews.get(interview_id)
    if not interview:
        return {
            "evaluation": "Let's continue with the next question.",
            "next_question": "Can you tell me more about your experience?",
            "raw_response": ""
        }
    
    config = interview["config"]
    interview_type = config.get("interview_type", "technical")
    
    # Build context from previous exchanges
    context_str = ""
    if conversation_context:
        recent_context = conversation_context[-3:]  # Last 3 exchanges
        for i, exchange in enumerate(recent_context):
            context_str += f"Q{i+1}: {exchange.get('question', '')}\n"
            context_str += f"A{i+1}: {exchange['candidate']}\n\n"

    if interview_type == "technical":
        # Handle technical interviews with categories
        technical_categories = interview.get('technical_categories', list(TECHNICAL_CATEGORIES.keys()))
        focus_areas = []
        for category in technical_categories:
            if category in TECHNICAL_CATEGORIES:
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
    else:
        # Handle role-based interviews
        role_type = config.get("role_type", "general")
        role_title = config.get("role_title", "Professional")
        company = config.get("company", "our company")
        specific_skills = config.get("specific_skills", [])
        interview_focus = config.get("interview_focus", [])
        
        skills_text = ", ".join(specific_skills) if specific_skills else "general professional skills"
        focus_text = ", ".join(interview_focus) if interview_focus else "overall experience and qualifications"
        
        system_prompt = (
            f"You are a professional interviewer conducting an interview for a {role_title} position at {company}.\n"
            f"Focus on these skills: {skills_text}\n"
            f"Interview focus areas: {focus_text}\n\n"
            f"Based on the conversation context and candidate's latest response, provide:\n"
            "1. Brief evaluation of their answer (2-3 sentences max)\n"
            "2. Next appropriate question related to the role and focus areas (concise, clear)\n\n"
            "Respond in JSON format:\n"
            '{\n  "evaluation": "brief feedback here",\n'
            '  "next_question": "your next question"\n}'
        )

    prompt = f"Context:\n{context_str}\nLatest candidate response: {candidate_text}"

    max_retries = 2
    for attempt in range(max_retries):
        try:
            chat_completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
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
                # Fallback: treat as plain text
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

def run_interview_with_websocket(websocket, interview_id: str, session_minutes: int, start_time: float):
    """Modified version of your interview logic that works with WebSocket"""
    conversation = []
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
            callback=lambda indata, frames, time_, status: audio_callback_websocket(indata, frames, time_, status),
            blocksize=int(SAMPLE_RATE * FRAME_DURATION_MS / 1000),
        ):
            while (time.time() - start_time) < session_minutes * 60:
                interview = active_interviews.get(interview_id)
                if not interview or interview["status"] in ["ended", "disconnected"]:
                    break
                    
                try:
                    audio_chunk = audio_queue.get(timeout=0.1)
                    if CHANNELS > 1:
                        audio_chunk = np.mean(audio_chunk, axis=1)
                    else:
                        audio_chunk = audio_chunk.flatten()
                except queue.Empty:
                    if not speech_active and (time.time() - last_prompt_time) > MAX_SILENCE_GAP:
                        nudge_messages = [
                            "I'm still waiting for your response. Please take your time.",
                            "Could you please share your thoughts on the question?",
                            "Feel free to think out loud or ask for clarification if needed."
                        ]
                        nudge_idx = (round_idx % len(nudge_messages))
                        nudge_msg = nudge_messages[nudge_idx]
                        
                        queue_websocket_message(
                            interview_id,
                            "interviewer_nudge",
                            {"message": nudge_msg}
                        )
                        
                        play_tts_websocket(nudge_msg, interview_id)
                        last_prompt_time = time.time()
                    continue

                # Process audio frames (using your existing VAD logic)
                for frame in frame_generator(FRAME_DURATION_MS, audio_chunk, SAMPLE_RATE):
                    if len(frame) < int(SAMPLE_RATE * FRAME_DURATION_MS / 1000):
                        continue

                    pcm_bytes = frame.tobytes()
                    try:
                        is_speech_frame = vad.is_speech(pcm_bytes, SAMPLE_RATE)
                    except Exception as e:
                        is_speech_frame = False

                    if is_speech_frame:
                        if not speech_active:
                            speech_start = time.time()
                            queue_websocket_message(
                                interview_id,
                                "listening",
                                {"message": "Listening..."}
                            )
                            print(f"🎙️ Started listening for interview {interview_id}")
                        
                        frame_int16 = frame.astype(np.int16)
                        buffer.append(frame_int16)
                        speech_active = True
                        silence_start = None
                    elif speech_active:
                        frame_int16 = frame.astype(np.int16)
                        buffer.append(frame_int16)

                        if silence_start is None:
                            silence_start = time.time()
                        elif (time.time() - silence_start) > SILENCE_THRESHOLD_SEC:
                            # Process the utterance
                            samples = np.concatenate(buffer) if buffer else np.array([], dtype=np.int16)
                            speech_duration = estimate_audio_duration(samples, SAMPLE_RATE)

                            if speech_duration >= MIN_SPEECH_DURATION:
                                round_idx += 1
                                filename = f"candidate_{interview_id}_{round_idx}.wav"

                                if save_wav(filename, samples, SAMPLE_RATE):
                                    queue_websocket_message(
                                        interview_id,
                                        "processing",
                                        {"message": f"Processing response {round_idx}", "duration": speech_duration}
                                    )

                                    transcript = transcribe_audio(filename)

                                    if transcript:
                                        response_data = interviewer_response_websocket(transcript, conversation, interview_id)

                                        conversation.append({
                                            "round": round_idx,
                                            "candidate": transcript,
                                            "evaluation": response_data.get("evaluation", ""),
                                            "next_question": response_data.get("next_question", ""),
                                            "timestamp": time.time() - start_time
                                        })

                                        # Update the stored conversation
                                        with interview_lock:
                                            active_interviews[interview_id]["conversation"] = conversation

                                        # Send transcript to client
                                        queue_websocket_message(
                                            interview_id,
                                            "candidate_response",
                                            {"transcript": transcript, "round": round_idx}
                                        )

                                        if response_data.get("next_question"):
                                            queue_websocket_message(
                                                interview_id,
                                                "interviewer_question",
                                                {"message": response_data["next_question"], "round": round_idx + 1}
                                            )
                                            
                                            play_tts_websocket(response_data["next_question"], interview_id)
                                            last_prompt_time = time.time()
                                    else:
                                        retry_msg = "I couldn't hear that clearly. Could you please repeat your answer?"
                                        queue_websocket_message(
                                            interview_id,
                                            "transcription_failed",
                                            {"message": retry_msg}
                                        )
                                        play_tts_websocket(retry_msg, interview_id)
                                        last_prompt_time = time.time()

                                    try:
                                        os.remove(filename)
                                    except Exception:
                                        pass

                            buffer = []
                            speech_active = False
                            silence_start = None

    except Exception as e:
        print(f"Interview error for {interview_id}: {e}")
    finally:
        # Generate final feedback
        try:
            generate_and_send_final_feedback(interview_id, conversation, start_time)
        except Exception as e:
            print(f"Error generating final feedback: {e}")
        
        # End interview
        queue_websocket_message(
            interview_id,
            "interview_ended",
            {"message": "Interview session completed"}
        )

async def send_websocket_message(websocket, message_type: str, data: Dict):
    """Send a message through WebSocket"""
    try:
        message = {
            "type": message_type,
            "timestamp": time.time(),
            **data
        }
        await websocket.send_json(message)
    except Exception as e:
        print(f"Failed to send WebSocket message: {e}")

def send_websocket_message_sync(websocket, message_type: str, data: Dict):
    """Send a message through WebSocket synchronously from a thread"""
    # This function is deprecated - we should use queue_websocket_message instead
    print(f"Warning: send_websocket_message_sync is deprecated. Use queue_websocket_message instead.")
    print(f"WebSocket message: {message_type} - {data.get('message', '')}")

def queue_websocket_message(interview_id: str, message_type: str, data: Dict):
    """Queue a message to be sent via WebSocket"""
    if interview_id in message_queues:
        message = {
            "type": message_type,
            "timestamp": time.time(),
            **data
        }
        try:
            message_queues[interview_id].put_nowait(message)
            print(f"Queued WebSocket message: {message_type} for {interview_id}")
        except queue.Full:
            print(f"Message queue full for interview {interview_id}")
    else:
        print(f"No message queue found for interview {interview_id}")

def generate_and_send_final_feedback(interview_id: str, conversation: list, start_time: float):
    """Generate and send final feedback for the interview"""
    try:
        interview = active_interviews.get(interview_id)
        config = interview["config"] if interview else {}
        interview_type = config.get("interview_type", "technical")
        
        # Build role-specific feedback prompt
        if interview_type == "technical":
            technical_categories = interview.get('technical_categories', []) if interview else []
            categories_text = ", ".join([cat.upper() for cat in technical_categories]) if technical_categories else "general technical topics"
            
            final_prompt = f"""
            Technical Interview Summary:
            Duration: {(time.time() - start_time)/60:.1f} minutes
            Total exchanges: {len(conversation)}
            Technical Focus: {categories_text}

            Conversation history:
            {json.dumps(conversation, indent=2)}

            Please provide comprehensive final feedback for this technical interview, including:
            1. Overall technical performance assessment
            2. Strengths demonstrated in the focus areas
            3. Areas for technical improvement
            4. Recommendation (hire/no hire/needs more evaluation)
            Keep it concise but thorough.
            """
            system_content = "You are a senior technical interviewer providing final comprehensive feedback."
        else:
            role_type = config.get("role_type", "general")
            role_title = config.get("role_title", "Professional")
            company = config.get("company", "our company")
            specific_skills = config.get("specific_skills", [])
            interview_focus = config.get("interview_focus", [])
            
            skills_text = ", ".join(specific_skills) if specific_skills else "general skills"
            focus_text = ", ".join(interview_focus) if interview_focus else "overall qualifications"
            
            final_prompt = f"""
            {role_title} Interview Summary:
            Company: {company}
            Role Type: {role_type}
            Duration: {(time.time() - start_time)/60:.1f} minutes
            Total exchanges: {len(conversation)}
            Skills Focus: {skills_text}
            Interview Focus: {focus_text}

            Conversation history:
            {json.dumps(conversation, indent=2)}

            Please provide comprehensive final feedback for this {role_title} interview, including:
            1. Overall performance assessment for the role
            2. Strengths demonstrated relevant to {role_type}
            3. Areas for improvement in the context of this role
            4. Recommendation (hire/no hire/needs more evaluation)
            Keep it concise but thorough.
            """
            system_content = f"You are a senior interviewer providing final comprehensive feedback for a {role_title} position."

        final_feedback = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": final_prompt}
            ],
            temperature=0.2,
            max_tokens=500,
        )

        feedback_text = final_feedback.choices[0].message.content
        
        # Send feedback via WebSocket
        queue_websocket_message(
            interview_id,
            "final_feedback",
            {"feedback": feedback_text, "summary": {
                "duration_minutes": (time.time() - start_time) / 60,
                "total_exchanges": len(conversation),
                "interview_type": interview_type,
                "role_title": config.get("role_title", "Technical Interview")
            }}
        )
        
        # Play feedback via TTS
        feedback_intro = "Thank you for the interview. Here is your final feedback: "
        play_tts_websocket(feedback_intro, interview_id)
        
        print(f"Final feedback generated for interview {interview_id}")
        
        # Save interview summary to file
        summary = {
            "interview_id": interview_id,
            "interview_type": interview_type,
            "role_title": config.get("role_title", "Technical Interview"),
            "company": config.get("company", ""),
            "duration_minutes": (time.time() - start_time) / 60,
            "total_exchanges": len(conversation),
            "conversation": conversation,
            "final_feedback": feedback_text,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "config": config
        }
        
        summary_filename = f"interview_summary_{interview_id}.json"
        with open(summary_filename, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"Interview summary saved to {summary_filename}")
        
    except Exception as e:
        print(f"Error generating final feedback: {e}")
        # Send error message
        queue_websocket_message(
            interview_id,
            "final_feedback",
            {"feedback": "Thank you for the interview. Feedback generation encountered an error.", "summary": {
                "duration_minutes": (time.time() - start_time) / 60,
                "total_exchanges": len(conversation)
            }}
        )

def audio_callback_websocket(indata, frames, time_, status):
    """Audio callback for WebSocket interviews"""
    if status:
        print(f"Audio status: {status}")
    if not is_playing_tts.is_set():
        audio_queue.put(indata.copy())

def play_tts_websocket(text: str, interview_id: str = None) -> bool:
    """WebSocket-safe TTS with proper flag management and fallback"""
    global fallback_tts_engine  # Declare global variable at the top
    
    if not text or not text.strip():
        return False

    try:
        is_playing_tts.set()  # Signal that TTS is playing
        
        # Send WebSocket notification that TTS is starting
        if interview_id:
            queue_websocket_message(
                interview_id,
                "tts_starting",
                {"message": "🔊 Playing audio response..."}
            )

        # Try primary TTS (PlayAI via Groq)
        try:
            response = client.audio.speech.create(
                model=TTS_MODEL,
                voice=VOICE,
                response_format="wav",
                input=text[:500],  # Limit length to avoid timeout
            )

            # Write binary content to temp file
            temp_path = Path("interviewer_ws.wav")
            with open(temp_path, "wb") as f:
                f.write(response.read())

            # Read and play
            data, sr = sf.read(str(temp_path), dtype="float32")
            sd.play(data, sr)
            sd.wait()
            
            # Clean up temp file
            try:
                temp_path.unlink()
            except:
                pass
                
            print(f"✅ PlayAI TTS completed for: {text[:50]}...")
            return True
            
        except Exception as primary_error:
            print(f"❌ PlayAI TTS error: {primary_error}")
            print("🔄 Switching to fallback TTS (pyttsx3)...")
            
            # Send WebSocket notification about fallback
            if interview_id:
                queue_websocket_message(
                    interview_id,
                    "tts_fallback",
                    {"message": "🔄 Using backup audio system..."}
                )
            
            # Fallback to pyttsx3 with timeout protection
            if fallback_tts_engine is not None:
                try:
                    print("🔄 Starting fallback TTS...")
                    # Ensure the engine is in a good state
                    fallback_tts_engine.stop()  # Stop any ongoing speech
                    
                    # Use threading with timeout to prevent hanging
                    import threading
                    import time
                    
                    def speak_with_timeout():
                        try:
                            fallback_tts_engine.say(text[:500])  # Limit length
                            fallback_tts_engine.runAndWait()
                            return True
                        except Exception as e:
                            print(f"❌ Error in speak_with_timeout: {e}")
                            return False
                    
                    # Create and start thread
                    speak_thread = threading.Thread(target=speak_with_timeout)
                    speak_thread.daemon = True
                    speak_thread.start()
                    
                    # Wait with timeout
                    speak_thread.join(timeout=10.0)  # 10 second timeout
                    
                    if speak_thread.is_alive():
                        print("⚠️ Fallback TTS timed out")
                        # Force stop the engine
                        try:
                            fallback_tts_engine.stop()
                        except:
                            pass
                        return False
                    else:
                        print(f"✅ Fallback TTS completed for: {text[:50]}...")
                        return True
                        
                except Exception as fallback_error:
                    print(f"❌ Fallback TTS error: {fallback_error}")
                    # Try to reinitialize the engine
                    try:
                        import pyttsx3
                        print("🔄 Reinitializing fallback TTS engine...")
                        fallback_tts_engine = pyttsx3.init()
                        voices = fallback_tts_engine.getProperty("voices")
                        if voices:
                            fallback_tts_engine.setProperty("voice", voices[1].id if len(voices) > 1 else voices[0].id)
                        fallback_tts_engine.setProperty("rate", 120)
                        fallback_tts_engine.setProperty("volume", 1.0)
                        
                        # Quick test with reinitialized engine
                        fallback_tts_engine.say("Audio system ready.")
                        fallback_tts_engine.runAndWait()
                        print(f"✅ Reinitialized fallback TTS completed")
                        return True
                    except Exception as reinit_error:
                        print(f"❌ Could not reinitialize fallback TTS: {reinit_error}")
            else:
                print("❌ Fallback TTS not available")
            
            return False
            
    except Exception as e:
        print(f"❌ Unexpected TTS error: {e}")
        return False
    finally:
        # CRITICAL: Force clear the TTS flag no matter what happened
        try:
            is_playing_tts.clear()
            print("🎙️ Audio capture resumed (TTS flag cleared)")
            
            # Additional safety: ensure fallback TTS is stopped
            if fallback_tts_engine is not None:
                try:
                    fallback_tts_engine.stop()
                except:
                    pass
                    
        except Exception as cleanup_error:
            print(f"❌ Cleanup error: {cleanup_error}")
            # Force flag clear even if other cleanup fails
            is_playing_tts.clear()
        
        # Send WebSocket notification that TTS is complete
        if interview_id:
            queue_websocket_message(
                interview_id,
                "tts_completed",
                {"message": "🎙️ Ready for your response"}
            )

def generate_interview_summary(interview: Dict) -> Dict:
    """Generate a summary of the interview session"""
    start_time = interview["start_time"]
    conversation = interview["conversation"]
    config = interview["config"]
    
    return {
        "interview_id": f"interview_{int(start_time)}",
        "candidate_name": config.get("candidate_name", "Unknown"),
        "interview_type": config.get("interview_type", "technical"),
        "duration_minutes": (time.time() - start_time) / 60,
        "total_exchanges": len(conversation),
        "conversation": conversation,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)),
        "end_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

if __name__ == "__main__":
    print("Starting AI Interview System...")
    print(f"API Key configured: {bool(groq_api_key)}")
    
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )