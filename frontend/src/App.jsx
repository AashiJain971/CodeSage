import { useState, useEffect } from 'react'
import './App.css'

// Components
import TypewriterIntro from './components/TypewriterIntro'
import Navbar from './components/Navbar'
import Hero from './components/Hero'
import Features from './components/Features'
import Footer from './components/Footer'

function App() {
  const [showIntro, setShowIntro] = useState(true)
  const [showMain, setShowMain] = useState(false)
  const [introFading, setIntroFading] = useState(false)

  const handleIntroComplete = () => {
    setIntroFading(true)
    // Start fading out intro immediately
    setTimeout(() => {
      setShowIntro(false)
      setShowMain(true)
    }, 200) // Very quick transition
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
          <Navbar />
          <Hero />
          <Features />
          <Footer />
        </div>
      )}
    </div>
  )
}

export default App
