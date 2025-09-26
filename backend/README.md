# AI Interview System - FastAPI Backend

This FastAPI application provides a WebSocket-based interface for conducting continuous AI interviews using your existing interview logic.

## Features

- **RESTful API** for managing interview sessions
- **WebSocket support** for real-time interview communication
- **Session management** with configurable duration
- **Audio processing** using your existing VAD and transcription logic
- **Conversation tracking** and summary generation
- **Web client** for testing the system

## API Endpoints

### REST Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status
- `POST /interview/start` - Start a new interview session
- `GET /interview/{interview_id}/status` - Get interview status
- `DELETE /interview/{interview_id}` - End interview session

### WebSocket Endpoint

- `WS /interview/{interview_id}/connect` - Real-time interview communication

## Installation & Setup

1. **Install dependencies** (already done):
   ```bash
   pip install fastapi uvicorn[standard] websockets python-multipart pydantic
   ```

2. **Ensure environment variables are set**:
   - Make sure your `.env` file contains `GROQ_API_KEY`

3. **Run the FastAPI server**:
   ```bash
   python main.py
   ```
   
   Or alternatively:
   ```bash
   uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```

4. **Access the system**:
   - API Documentation: http://127.0.0.1:8000/docs
   - Test Client: Open `test_client.html` in your browser

## Usage

### Using the Web Test Client

1. Open `test_client.html` in your browser
2. Click "Start Interview" to create a new session
3. Click "Connect" to join the interview via WebSocket
4. Speak when prompted - the system will automatically detect your voice
5. Click "End Interview" when finished

### Using the API Directly

1. **Start an interview**:
   ```bash
   curl -X POST "http://127.0.0.1:8000/interview/start" \
        -H "Content-Type: application/json" \
        -d '{
          "session_minutes": 10,
          "candidate_name": "Test User",
          "interview_type": "technical"
        }'
   ```

2. **Connect via WebSocket** using the returned interview ID
3. **Check status**:
   ```bash
   curl "http://127.0.0.1:8000/interview/{interview_id}/status"
   ```

## WebSocket Message Types

### Incoming (from server):
- `interview_started` - Interview session began
- `interviewer_question` - New question from interviewer
- `listening` - System is listening for response
- `processing` - Processing candidate response
- `candidate_response` - Transcribed candidate response
- `interviewer_nudge` - Prompt for inactive candidate
- `transcription_failed` - Could not transcribe audio
- `interview_ended` - Session completed

### Outgoing (to server):
- `ping` - Keep connection alive
- `end_interview` - Request to end session

## Configuration

The system uses the same configuration as your original `test.py`:

- `SAMPLE_RATE = 16000`
- `CHANNELS = 1`
- `FRAME_DURATION_MS = 20`
- `SESSION_MINUTES = 10` (configurable per session)
- `SILENCE_THRESHOLD_SEC = 1`
- `MIN_SPEECH_DURATION = 0.8`
- `MAX_SILENCE_GAP = 3.0`

## Interview Flow

1. **Session Creation**: Client creates interview via REST API
2. **WebSocket Connection**: Client connects to interview WebSocket
3. **Interview Start**: System plays opening question
4. **Continuous Loop**:
   - Voice Activity Detection (VAD) listens for speech
   - Audio transcription when speech ends
   - LLM generates next question/feedback
   - Text-to-Speech plays response
   - Process repeats until time limit or manual end
5. **Session End**: Generate summary and cleanup

## File Structure

```
backend/
├── main.py              # FastAPI application
├── test.py              # Original interview logic
├── test_client.html     # Web test client
├── README.md           # This file
└── interview_summary_*.json  # Generated interview summaries
```

## Notes

- The system preserves all your existing interview logic from `test.py`
- Multiple concurrent interviews are supported
- Audio files are automatically cleaned up after processing
- Interview summaries are saved as JSON files
- WebSocket connections are automatically managed
- Fallback TTS (pyttsx3) is used when PlayAI TTS fails

## Troubleshooting

1. **CORS Issues**: Adjust CORS settings in `main.py` for your domain
2. **Audio Issues**: Ensure microphone permissions are granted
3. **API Key Issues**: Check that `GROQ_API_KEY` is properly set
4. **Port Conflicts**: Change port in `main.py` if 8000 is in use

## Development

To extend the system:
- Add new WebSocket message types in `handle_websocket_message()`
- Modify interview logic in `run_interview_with_websocket()`
- Add new REST endpoints as needed
- Customize the web client for your UI requirements
