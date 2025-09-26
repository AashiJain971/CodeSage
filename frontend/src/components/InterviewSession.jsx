import { useState, useEffect, useRef } from 'react'
import Editor from '@monaco-editor/react'
import { 
  Video, 
  VideoOff, 
  Mic, 
  MicOff, 
  Monitor,
  Upload,
  Play,
  Square,
  FileText,
  Code as CodeIcon,
  MessageCircle,
} from 'lucide-react'
import { audioAPI, interviewAPI } from '../lib/api'
import './InterviewSession.css'

const InterviewSession = ({ interview, onEndInterview }) => {
  // Video & Audio State
  const [isVideoOn, setIsVideoOn] = useState(true)
  const [isAudioOn, setIsAudioOn] = useState(true)
  const [isScreenSharing, setIsScreenSharing] = useState(false)
  
  // Resume State
  const [resumeUploaded, setResumeUploaded] = useState(false)
  const [resumeFile, setResumeFile] = useState(null)
  const [uploadingResume, setUploadingResume] = useState(false)
  
  // Interview State
  const [interviewStarted, setInterviewStarted] = useState(false)
  const [captions, setCaptions] = useState([])
  const [currentQuestion, setCurrentQuestion] = useState('')
  
  // Code Editor State (for technical interviews)
  const [code, setCode] = useState('// Write your solution here\n')
  const [language, setLanguage] = useState('javascript')
  const [isRunning, setIsRunning] = useState(false)
  const [codeOutput, setCodeOutput] = useState('')
  
  // WebSocket & Media
  const wsRef = useRef(null)
  const videoRef = useRef(null)
  const mediaStreamRef = useRef(null)

  useEffect(() => {
    if (interviewStarted) {
      initializeMediaAndWebSocket()
    }
    
    return () => {
      cleanup()
    }
  }, [interviewStarted])

  const initializeMediaAndWebSocket = async () => {
    try {
      // Initialize camera and microphone
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: true, 
        audio: true 
      })
      mediaStreamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }

      // Initialize WebSocket connection
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
      wsRef.current = new WebSocket(`${wsUrl}/ws/interview/${interview.id}`)
      
      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data)
        handleWebSocketMessage(data)
      }
    } catch (error) {
      console.error('Error initializing media/websocket:', error)
    }
  }

  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'question':
        setCurrentQuestion(data.content)
        addCaption('Interviewer', data.content)
        break
      case 'transcript':
        addCaption('Candidate', data.content)
        break
      default:
        break
    }
  }

  const addCaption = (speaker, content) => {
    setCaptions(prev => [...prev.slice(-4), { speaker, content, timestamp: Date.now() }])
  }

  const cleanup = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop())
    }
    if (wsRef.current) {
      wsRef.current.close()
    }
  }

  const handleResumeUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    setUploadingResume(true)
    try {
      await audioAPI.uploadFile('/resume/upload', file)
      setResumeFile(file)
      setResumeUploaded(true)
    } catch (error) {
      console.error('Resume upload failed:', error)
      alert('Resume upload failed. Please try again.')
    } finally {
      setUploadingResume(false)
    }
  }

  const startInterview = async () => {
    if (!resumeUploaded) {
      alert('Please upload your resume before starting the interview.')
      return
    }
    
    try {
      await interviewAPI.startInterview({
        type: interview.type,
        category: interview.id
      })
      setInterviewStarted(true)
    } catch (error) {
      console.error('Failed to start interview:', error)
    }
  }

  const runCode = async () => {
    setIsRunning(true)
    try {
      const response = await fetch('/api/code/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, language })
      })
      const result = await response.text()
      setCodeOutput(result)
    } catch (error) {
      setCodeOutput('Error executing code: ' + error.message)
    } finally {
      setIsRunning(false)
    }
  }

  const toggleScreenShare = async () => {
    try {
      if (!isScreenSharing) {
        const screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true })
        setIsScreenSharing(true)
        // Handle screen sharing logic
      } else {
        setIsScreenSharing(false)
        // Stop screen sharing
      }
    } catch (error) {
      console.error('Screen share error:', error)
    }
  }

  return (
    <div className="interview-session">
      {/* Header */}
      <div className="session-header">
        <div className="session-header-content">
          <div>
            <h1 className="session-title">{interview.title}</h1>
            <p className="session-subtitle">
              {interviewStarted ? 'Interview in progress' : 'Preparing for interview'}
            </p>
          </div>
          <button
            onClick={onEndInterview}
            className="end-interview-btn"
          >
            End Interview
          </button>
        </div>
      </div>

      <div className="session-content">
        
        {/* Left Column: Video & Controls */}
        <div className="session-left">
          
          {/* Video Area */}
          <div className="video-section">
            <div className="video-grid">
              
              {/* Candidate Video */}
              <div className="video-container">
                <div className="video-feed">
                  {isVideoOn ? (
                    <video
                      ref={videoRef}
                      autoPlay
                      muted
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                  ) : (
                    <VideoOff size={48} color="#9ca3af" />
                  )}
                </div>
                <div className="video-label">You</div>
              </div>

              {/* Interviewer Video (Placeholder) */}
              <div className="video-container">
                <div className="video-feed video-placeholder">
                  <div className="ai-interviewer-avatar">AI</div>
                  <p style={{ fontWeight: 500 }}>CodeSage AI Interviewer</p>
                </div>
                <div className="video-label">Interviewer</div>
              </div>
            </div>

            {/* Video Controls */}
            <div className="video-controls">
              <button
                onClick={() => setIsVideoOn(!isVideoOn)}
                className={`control-btn ${!isVideoOn ? 'active' : ''}`}
              >
                {isVideoOn ? <Video size={20} /> : <VideoOff size={20} />}
              </button>
              
              <button
                onClick={() => setIsAudioOn(!isAudioOn)}
                className={`control-btn ${!isAudioOn ? 'active' : ''}`}
              >
                {isAudioOn ? <Mic size={20} /> : <MicOff size={20} />}
              </button>
              
              <button
                onClick={toggleScreenShare}
                className={`control-btn ${isScreenSharing ? 'screen-share' : ''}`}
              >
                <Monitor size={20} />
              </button>
            </div>
          </div>

          {/* Live Captions */}
          <div className="captions-section">
            <h3 className="captions-header">
              <MessageCircle size={20} />
              Live Captions
            </h3>
            <div className="captions-list">
              {captions.map((caption, index) => (
                <div
                  key={caption.timestamp}
                  className={`caption-item ${caption.speaker === 'Interviewer' ? 'interviewer' : 'candidate'}`}
                >
                  <div className="caption-speaker">
                    {caption.speaker}
                  </div>
                  <div className="caption-content">{caption.content}</div>
                </div>
              ))}
              {captions.length === 0 && (
                <div className="captions-empty">
                  Captions will appear here during the interview
                </div>
              )}
            </div>
          </div>

          {/* Code Editor (Technical Interviews Only) */}
          {interview.type === 'technical' && (
            <div className="code-editor-section">
              <div className="code-editor-header">
                <h3 className="code-editor-title">
                  <CodeIcon size={20} />
                  Code Editor
                </h3>
                <div className="code-editor-controls">
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="language-select"
                  >
                    <option value="javascript">JavaScript</option>
                    <option value="python">Python</option>
                    <option value="java">Java</option>
                    <option value="cpp">C++</option>
                  </select>
                  <button
                    onClick={runCode}
                    disabled={isRunning}
                    className="run-code-btn"
                  >
                    {isRunning ? <Square size={16} /> : <Play size={16} />}
                    {isRunning ? 'Running...' : 'Run Code'}
                  </button>
                </div>
              </div>
              
              <div className="code-editor-container">
                <Editor
                  height="300px"
                  language={language}
                  value={code}
                  onChange={setCode}
                  theme="vs-light"
                  options={{
                    fontSize: 14,
                    minimap: { enabled: false },
                    scrollBeyondLastLine: false,
                    automaticLayout: true
                  }}
                />
              </div>
              
              {codeOutput && (
                <div className="code-output">
                  <h4>Output:</h4>
                  <pre>{codeOutput}</pre>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Resume Upload & Controls */}
        <div className="session-right">
          
          {/* Resume Upload */}
          <div className="resume-section">
            <h3 className="resume-header">
              <FileText size={20} />
              Resume Upload
            </h3>
            
            {!resumeUploaded ? (
              <div>
                <input
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={handleResumeUpload}
                  style={{ display: 'none' }}
                  id="resume-upload"
                  disabled={uploadingResume}
                />
                <label
                  htmlFor="resume-upload"
                  className="resume-upload-area"
                >
                  <Upload size={32} className="resume-upload-icon" />
                  <div className="resume-upload-text">
                    {uploadingResume ? 'Uploading...' : 'Click to upload resume'}
                  </div>
                  <div className="resume-upload-subtext">
                    PDF, DOC, or DOCX (max 5MB)
                  </div>
                </label>
              </div>
            ) : (
              <div className="resume-success">
                <FileText size={20} />
                <div>
                  <div className="resume-success-title">Resume uploaded successfully</div>
                  <div className="resume-success-filename">
                    {resumeFile?.name}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Start Interview Button */}
          {!interviewStarted && (
            <div className="start-interview-section">
              <button
                onClick={startInterview}
                disabled={!resumeUploaded}
                className="start-interview-btn"
              >
                Start Interview
              </button>
            </div>
          )}

          {/* Current Question */}
          {currentQuestion && (
            <div className="current-question-section">
              <h3 className="current-question-header">
                Current Question
              </h3>
              <div className="current-question-content">
                {currentQuestion}
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  )
}

export default InterviewSession