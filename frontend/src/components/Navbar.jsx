import { useState, useEffect } from 'react'
import './Navbar.css'

const Navbar = ({ onTakeInterview }) => {
  const [isScrolled, setIsScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50)
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const navLinks = [
    { href: '#home', label: 'Home' },
    { href: '#interview', label: 'Take Interview', onClick: onTakeInterview },
    { href: '#past-interviews', label: 'Past Interviews' },
    { href: '#results', label: 'Results' },
    { href: '#upload', label: 'Upload Resume' }
  ]

  return (
    <nav className={`navbar ${isScrolled ? 'navbar-scrolled' : ''}`}>
      <div className="container">
        <div className="navbar-content">
          <div className="navbar-brand">
            <span className="brand-text">CodeSage</span>
          </div>
          
          <div className="navbar-links">
            {navLinks.map((link, index) => (
              <a 
                key={index} 
                href={link.href} 
                className="nav-link"
                onClick={link.onClick ? (e) => { e.preventDefault(); link.onClick(); } : undefined}
              >
                {link.label}
              </a>
            ))}
          </div>

          <div className="navbar-mobile">
            <button className="mobile-menu-btn">
              <span></span>
              <span></span>
              <span></span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar