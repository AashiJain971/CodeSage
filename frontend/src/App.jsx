import { useState, useEffect } from 'react'
import './App.css'

// Components
import TypewriterIntro from './components/TypewriterIntro'
import Navbar from './components/Navbar'
import Hero from './components/Hero'
import Features from './components/Features'
import Footer from './components/Footer'
import InterviewSelection from './components/InterviewSelection'
import InterviewSession from './components/InterviewSession'

function App() {
  const [showIntro, setShowIntro] = useState(true)
  const [showMain, setShowMain] = useState(false)
  const [currentView, setCurrentView] = useState('landing') // 'landing', 'selection', 'session'
  const [selectedInterview, setSelectedInterview] = useState(null)
  const [introFading, setIntroFading] = useState(false)

  const handleIntroComplete = () => {
    setIntroFading(true)
    // Start fading out intro immediately
    setTimeout(() => {
      setShowIntro(false)
      setShowMain(true)
    }, 200) // Very quick transition
  }

  const handleStartInterview = (interview) => {
    setSelectedInterview(interview)
    setCurrentView('session')
  }

  const handleEndInterview = () => {
    setSelectedInterview(null)
    setCurrentView('landing')
  }

  const navigateToInterviews = () => {
    setCurrentView('selection')
  }

  return (
    <div className="app">
      {showIntro && (
        <div className={`intro-wrapper ${introFading ? 'fade-out' : ''}`}>
          <TypewriterIntro onComplete={handleIntroComplete} />
        </div>
      )}
      
      {showMain && (
        <div className="main-content fade-in-fast">
          {currentView === 'landing' && (
            <>
              <Navbar onTakeInterview={navigateToInterviews} />
              <Hero onTakeInterview={navigateToInterviews} />
              <Features />
              <Footer />
            </>
          )}
          
          {currentView === 'selection' && (
            <InterviewSelection onStartInterview={handleStartInterview} />
          )}
          
          {currentView === 'session' && selectedInterview && (
            <InterviewSession 
              interview={selectedInterview} 
              onEndInterview={handleEndInterview} 
            />
          )}
        </div>
      )}
    </div>
  )
}

export default App
