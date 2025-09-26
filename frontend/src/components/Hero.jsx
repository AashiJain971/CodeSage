import './Hero.css'

const Hero = () => {
  return (
    <section className="hero section" id="home">
      <div className="animated-bg"></div>
      <div className="particles">
        {[...Array(30)].map((_, i) => (
          <div
            key={i}
            className="particle"
            style={{
              left: Math.random() * 100 + '%',
              animationDelay: Math.random() * 20 + 's',
              width: Math.random() * 6 + 3 + 'px',
              height: Math.random() * 6 + 3 + 'px',
              animationDuration: (Math.random() * 15 + 20) + 's'
            }}
          />
        ))}
      </div>
      
      <div className="container">
        <div className="hero-content">
          <div className="hero-left slide-up">
            <h1 className="hero-title">
              Redefining Interview Preparation
            </h1>
            <p className="hero-subtitle">
              Experience the future of interview practice with AI-powered mock interviews, 
              intelligent feedback, and personalized learning paths.
            </p>
            <div className="hero-buttons">
              <a href="#interview" className="btn btn-primary glow-on-hover">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polygon points="5,3 19,12 5,21 5,3"></polygon>
                </svg>
                Start Interview
              </a>
              <a href="#upload" className="btn btn-secondary">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14,2 14,8 20,8"></polyline>
                  <line x1="16" y1="13" x2="8" y2="13"></line>
                  <line x1="16" y1="17" x2="8" y2="17"></line>
                  <polyline points="10,9 9,9 8,9"></polyline>
                </svg>
                Upload Resume
              </a>
            </div>
          </div>
          
          <div className="hero-right slide-up">
            <div className="hero-illustration">
              <div className="floating-card card-1">
                <div className="card-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M9 12l2 2 4-4"></path>
                    <circle cx="12" cy="12" r="9"></circle>
                  </svg>
                </div>
                <span>AI Analysis</span>
              </div>
              
              <div className="floating-card card-2">
                <div className="card-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 20h9"></path>
                    <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
                  </svg>
                </div>
                <span>Smart Feedback</span>
              </div>
              
              <div className="floating-card card-3">
                <div className="card-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="22,12 18,12 15,21 9,3 6,12 2,12"></polyline>
                  </svg>
                </div>
                <span>Performance Tracking</span>
              </div>
              
              <div className="hero-main-visual">
                <div className="brain-container">
                  <div className="brain-outline"></div>
                  <div className="neural-network">
                    <div className="neural-node node-1"></div>
                    <div className="neural-node node-2"></div>
                    <div className="neural-node node-3"></div>
                    <div className="neural-node node-4"></div>
                    <div className="neural-connection conn-1"></div>
                    <div className="neural-connection conn-2"></div>
                    <div className="neural-connection conn-3"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default Hero