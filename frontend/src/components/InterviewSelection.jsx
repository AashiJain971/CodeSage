import { useState, useEffect } from 'react'
import { 
  Code, 
  Briefcase, 
  Users, 
  Brain, 
  Laptop, 
  PlayCircle,
  ChevronRight
} from 'lucide-react'
import { interviewAPI } from '../lib/api'
import './InterviewSelection.css'

const InterviewSelection = ({ onStartInterview }) => {
  const [interviewTypes, setInterviewTypes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchInterviewTypes()
  }, [])

  const fetchInterviewTypes = async () => {
    try {
      setLoading(true)
      // Fetch from backend API
      const response = await interviewAPI.getCategories()
      setInterviewTypes(response.data || response)
    } catch (err) {
      console.error('Failed to fetch interview types:', err)
      // Fallback to mock data if API fails
      setInterviewTypes([
        {
          id: 'software-engineer-technical',
          title: 'Software Engineer – Technical',
          description: 'Algorithmic problems, data structures, and coding challenges',
          type: 'technical',
          icon: 'code',
          duration: '45-60 minutes',
          skills: ['Algorithms', 'Data Structures', 'System Design']
        },
        {
          id: 'product-manager-role',
          title: 'Product Manager – Role-based',
          description: 'Product strategy, market analysis, and leadership scenarios',
          type: 'role-based',
          icon: 'briefcase',
          duration: '30-45 minutes',
          skills: ['Strategy', 'Analytics', 'Communication']
        },
        {
          id: 'data-scientist-technical',
          title: 'Data Scientist – Technical',
          description: 'Machine learning, statistics, and data analysis',
          type: 'technical',
          icon: 'brain',
          duration: '45-60 minutes',
          skills: ['ML/AI', 'Statistics', 'Python/R']
        },
        {
          id: 'frontend-developer',
          title: 'Frontend Developer – Technical',
          description: 'React, JavaScript, CSS, and web development challenges',
          type: 'technical',
          icon: 'laptop',
          duration: '40-50 minutes',
          skills: ['React', 'JavaScript', 'CSS']
        },
        {
          id: 'general-interview',
          title: 'General Interview',
          description: 'Behavioral questions and general assessment',
          type: 'role-based',
          icon: 'users',
          duration: '30 minutes',
          skills: ['Communication', 'Problem Solving', 'Leadership']
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  const getIcon = (iconName) => {
    const iconMap = {
      code: Code,
      briefcase: Briefcase,
      brain: Brain,
      laptop: Laptop,
      users: Users
    }
    const IconComponent = iconMap[iconName] || Code
    return <IconComponent size={24} />
  }

  const getCardClass = (index, type) => {
    const baseClass = 'interview-card'
    const colorClasses = ['', 'violet', 'magenta', '', 'violet']
    return `${baseClass} ${colorClasses[index % colorClasses.length]}`
  }

  const getButtonClass = (index, type) => {
    const baseClass = 'card-button'
    const colorClasses = ['', 'violet', '', '', 'violet']
    return `${baseClass} ${colorClasses[index % colorClasses.length]}`
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
      </div>
    )
  }

  return (
    <div className="interview-selection">
      {/* Header */}
      <div className="selection-header">
        <h1 className="selection-title">
          Choose Your Interview
        </h1>
        <p className="selection-subtitle">
          Select from general role-based or technical interviews tailored to your career goals
        </p>
      </div>

      {/* Interview Options Grid */}
      <div className="interview-grid">
        {interviewTypes.map((interview, index) => (
          <div
            key={interview.id}
            className={getCardClass(index, interview.type)}
            onClick={() => onStartInterview(interview)}
          >
            {/* Icon & Type Badge */}
            <div className="card-header">
              <div className="card-icon">
                {getIcon(interview.icon)}
              </div>
              <span className={`card-badge ${interview.type === 'technical' ? '' : 'violet'}`}>
                {interview.type}
              </span>
            </div>

            {/* Title */}
            <h3 className="card-title">
              {interview.title}
            </h3>

            {/* Description */}
            <p className="card-description">
              {interview.description}
            </p>

            {/* Duration & Skills */}
            <div className="card-meta">
              <div className="card-duration">
                Duration: {interview.duration}
              </div>
              <div className="card-skills">
                {interview.skills.map((skill, idx) => (
                  <span key={idx} className="skill-tag">
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            {/* Start Button */}
            <button className={getButtonClass(index, interview.type)}>
              <PlayCircle size={20} />
              Start Interview
              <ChevronRight size={16} />
            </button>
          </div>
        ))}
      </div>

      {/* Error State */}
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
    </div>
  )
}

export default InterviewSelection