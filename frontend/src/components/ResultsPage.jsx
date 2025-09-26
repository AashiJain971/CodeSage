// ResultsPage.jsx - Interview Results Dashboard
import { useState } from 'react';
import { 
  BarChart, Bar, LineChart, Line, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell 
} from 'recharts';

// Inline CSS styles
const styles = {
  container: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
  },
  mainContent: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '0 20px 40px',
  },
  header: {
    background: 'rgba(255, 255, 255, 0.1)',
    backdropFilter: 'blur(10px)',
    borderBottom: '1px solid rgba(255, 255, 255, 0.2)',
    padding: '24px 0',
    marginBottom: '32px',
  },
  headerContent: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '0 20px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: '20px',
  },
  avatarSection: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  avatar: {
    width: '60px',
    height: '60px',
    borderRadius: '50%',
    background: 'linear-gradient(45deg, #ff6b6b, #feca57)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '24px',
    fontWeight: 'bold',
    color: 'white',
  },
  candidateInfo: {
    display: 'flex',
    flexDirection: 'column',
  },
  name: {
    margin: '0',
    fontSize: '28px',
    fontWeight: '700',
    color: 'white',
    lineHeight: '1.2',
  },
  role: {
    margin: '4px 0 0 0',
    fontSize: '16px',
    color: 'rgba(255, 255, 255, 0.8)',
    fontWeight: '400',
  },
  summary: {
    maxWidth: '400px',
    color: 'rgba(255, 255, 255, 0.9)',
    fontSize: '14px',
    lineHeight: '1.5',
  },
  tabNav: {
    background: 'rgba(255, 255, 255, 0.1)',
    backdropFilter: 'blur(10px)',
    borderBottom: '1px solid rgba(255, 255, 255, 0.2)',
    padding: '0',
    marginBottom: '32px',
  },
  tabContainer: {
    maxWidth: '1200px',
    margin: '0 auto',
    display: 'flex',
    gap: '8px',
    padding: '0 20px',
  },
  tab: {
    background: 'transparent',
    border: 'none',
    color: 'rgba(255, 255, 255, 0.7)',
    padding: '16px 24px',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
    borderBottom: '2px solid transparent',
    transition: 'all 0.3s ease',
  },
  activeTab: {
    color: 'white',
    borderBottomColor: '#feca57',
    background: 'rgba(255, 255, 255, 0.1)',
  },
  overviewGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '24px',
    marginBottom: '32px',
  },
  scoreCard: {
    background: 'white',
    borderRadius: '12px',
    padding: '24px',
    textAlign: 'center',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
  },
  scoreTitle: {
    margin: '0 0 20px 0',
    fontSize: '20px',
    fontWeight: '600',
    color: '#333',
  },
  scoreCircle: {
    position: 'relative',
    margin: '20px 0',
    display: 'inline-block',
  },
  scoreText: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    textAlign: 'center',
  },
  score: {
    display: 'block',
    fontSize: '32px',
    fontWeight: '700',
    color: '#333',
    lineHeight: '1',
  },
  scoreLabel: {
    display: 'block',
    fontSize: '12px',
    color: '#666',
    marginTop: '4px',
  },
  skillsCard: {
    background: 'white',
    borderRadius: '12px',
    padding: '24px',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
  },
  sectionTitle: {
    margin: '0 0 20px 0',
    fontSize: '20px',
    fontWeight: '600',
    color: '#333',
  },
  skillItem: {
    marginBottom: '16px',
  },
  skillHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '8px',
  },
  skillName: {
    fontSize: '14px',
    fontWeight: '500',
    color: '#333',
  },
  skillValue: {
    fontSize: '14px',
    fontWeight: '600',
    color: '#667eea',
  },
  progressBar: {
    height: '8px',
    background: '#f0f0f0',
    borderRadius: '4px',
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    background: 'linear-gradient(90deg, #667eea, #764ba2)',
    borderRadius: '4px',
    transition: 'width 0.5s ease',
  },
  chartsGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '24px',
    marginBottom: '32px',
  },
  chartCard: {
    background: 'white',
    borderRadius: '12px',
    padding: '24px',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
    height: '300px',
  },
  swotGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gridTemplateRows: '1fr 1fr',
    gap: '20px',
    marginBottom: '32px',
  },
  swotCard: {
    background: 'white',
    borderRadius: '12px',
    padding: '20px',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
    borderTop: '4px solid',
  },
  swotTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    margin: '0 0 16px 0',
    fontSize: '16px',
    fontWeight: '600',
  },
  swotList: {
    margin: '0',
    paddingLeft: '20px',
  },
  swotItem: {
    marginBottom: '8px',
    fontSize: '14px',
    lineHeight: '1.4',
  },
  historyCard: {
    background: 'white',
    borderRadius: '12px',
    padding: '24px',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
    marginBottom: '32px',
  },
  historyTable: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  tableHeader: {
    borderBottom: '1px solid #e0e0e0',
  },
  tableHeaderCell: {
    padding: '12px 16px',
    textAlign: 'left',
    fontSize: '14px',
    fontWeight: '600',
    color: '#666',
  },
  tableRow: {
    borderBottom: '1px solid #f5f5f5',
  },
  tableCell: {
    padding: '12px 16px',
    fontSize: '14px',
    color: '#333',
  },
  viewButton: {
    background: 'linear-gradient(135deg, #667eea, #764ba2)',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    padding: '6px 12px',
    fontSize: '12px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
  },
  recommendationsCard: {
    background: 'white',
    borderRadius: '12px',
    padding: '24px',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
  },
  recommendationText: {
    fontSize: '14px',
    lineHeight: '1.6',
    color: '#333',
    marginBottom: '12px',
  },
  fullWidth: {
    gridColumn: '1 / -1',
  },
};

// Helper function to apply responsive styles
const getStyle = (styleKey, isMobile = false) => {
  const baseStyle = styles[styleKey];
  return baseStyle;
};

// Mock data
const mockData = {
  candidate: {
    name: 'Sarah Johnson',
    role: 'Frontend Developer',
    summary: 'Strong technical skills with excellent communication abilities. Shows great potential for senior roles.',
  },
  overallScore: 82,
  skills: [
    { name: 'JavaScript', score: 85 },
    { name: 'React', score: 90 },
    { name: 'Communication', score: 78 },
    { name: 'Problem Solving', score: 88 },
    { name: 'Teamwork', score: 75 },
  ],
  performanceHistory: [
    { date: 'Jan 2023', score: 75 },
    { date: 'Apr 2023', score: 78 },
    { date: 'Jul 2023', score: 80 },
    { date: 'Oct 2023', score: 82 },
  ],
  skillDistribution: [
    { subject: 'Technical', score: 85 },
    { subject: 'Communication', score: 78 },
    { subject: 'Leadership', score: 70 },
    { subject: 'Problem Solving', score: 88 },
    { subject: 'Adaptability', score: 82 },
  ],
  swotAnalysis: {
    strengths: [
      'Strong technical knowledge in React and JavaScript',
      'Excellent problem-solving abilities',
      'Good communication skills during technical explanations'
    ],
    weaknesses: [
      'Limited experience with backend technologies',
      'Could improve time management on complex tasks',
      'Needs more confidence in leadership situations'
    ],
    opportunities: [
      'Growing demand for React developers in the market',
      'Potential to lead small projects with mentorship',
      'Opportunity to learn Node.js for full-stack development'
    ],
    threats: [
      'Increasing competition in the frontend job market',
      'Rapidly changing JavaScript ecosystem requires constant learning',
      'AI tools automating some frontend tasks'
    ]
  },
  interviewHistory: [
    { id: 1, date: '2023-10-15', role: 'Senior Frontend Developer', score: 82 },
    { id: 2, date: '2023-07-20', role: 'Frontend Developer', score: 80 },
    { id: 3, date: '2023-04-10', role: 'React Developer', score: 78 },
    { id: 4, date: '2023-01-05', role: 'Junior Frontend Developer', score: 75 },
  ],
  recommendations: [
    'Focus on learning backend technologies like Node.js to become a full-stack developer.',
    'Practice leadership skills by mentoring junior developers or leading small projects.',
    'Continue building complex projects to strengthen problem-solving abilities.',
    'Stay updated with the latest React features and best practices.',
    'Improve time management skills by using productivity techniques like Pomodoro.'
  ]
};

// Header Component
const Header = ({ candidate }) => (
  <header style={getStyle('header')}>
    <div style={getStyle('headerContent')}>
      <div style={getStyle('avatarSection')}>
        <div style={getStyle('avatar')}>
          {candidate.name.charAt(0)}
        </div>
        <div style={getStyle('candidateInfo')}>
          <h1 style={getStyle('name')}>{candidate.name}</h1>
          <p style={getStyle('role')}>{candidate.role}</p>
        </div>
      </div>
      <div style={getStyle('summary')}>
        <p>{candidate.summary}</p>
      </div>
    </div>
  </header>
);

// Tab Navigation Component
const TabNavigation = ({ activeTab, onTabChange }) => {
  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'skills', label: 'Skills' },
    { id: 'history', label: 'History' },
    { id: 'swot', label: 'SWOT Analysis' },
  ];

  return (
    <nav style={getStyle('tabNav')}>
      <div style={getStyle('tabContainer')}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            style={{
              ...getStyle('tab'),
              ...(activeTab === tab.id ? getStyle('activeTab') : {})
            }}
            onClick={() => onTabChange(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
    </nav>
  );
};

// Score Card Component
const ScoreCard = ({ score }) => {
  const circumference = 2 * Math.PI * 45;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div style={getStyle('scoreCard')}>
      <h3 style={getStyle('scoreTitle')}>Overall Score</h3>
      <div style={getStyle('scoreCircle')}>
        <svg width="120" height="120" viewBox="0 0 120 120">
          <circle
            cx="60"
            cy="60"
            r="45"
            stroke="#e0e0e0"
            strokeWidth="8"
            fill="none"
          />
          <circle
            cx="60"
            cy="60"
            r="45"
            stroke="url(#scoreGradient)"
            strokeWidth="8"
            fill="none"
            strokeDasharray={strokeDasharray}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            transform="rotate(-90 60 60)"
          />
          <defs>
            <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#667eea" />
              <stop offset="100%" stopColor="#764ba2" />
            </linearGradient>
          </defs>
        </svg>
        <div style={getStyle('scoreText')}>
          <span style={getStyle('score')}>{score}</span>
          <span style={getStyle('scoreLabel')}>out of 100</span>
        </div>
      </div>
      <p>Excellent performance! You're in the top 20% of candidates.</p>
    </div>
  );
};

// Skills Section Component
const SkillsSection = ({ compact = false }) => {
  const skillsToShow = compact ? mockData.skills.slice(0, 3) : mockData.skills;
  
  return (
    <div style={getStyle('skillsCard')}>
      <h3 style={getStyle('sectionTitle')}>
        {compact ? 'Top Skills' : 'Skills Assessment'}
      </h3>
      {skillsToShow.map((skill, index) => (
        <div key={index} style={getStyle('skillItem')}>
          <div style={getStyle('skillHeader')}>
            <span style={getStyle('skillName')}>{skill.name}</span>
            <span style={getStyle('skillValue')}>{skill.score}%</span>
          </div>
          <div style={getStyle('progressBar')}>
            <div 
              style={{
                ...getStyle('progressFill'),
                width: `${skill.score}%`
              }} 
            />
          </div>
        </div>
      ))}
    </div>
  );
};

// Charts Section Component
const ChartsSection = () => (
  <div style={getStyle('chartsGrid')}>
    <div style={getStyle('chartCard')}>
      <h3 style={getStyle('sectionTitle')}>Performance History</h3>
      <ResponsiveContainer width="100%" height="85%">
        <LineChart data={mockData.performanceHistory}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="date" />
          <YAxis domain={[70, 100]} />
          <Tooltip />
          <Line 
            type="monotone" 
            dataKey="score" 
            stroke="#667eea" 
            strokeWidth={2}
            dot={{ fill: '#667eea', strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6, fill: '#764ba2' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
    
    <div style={getStyle('chartCard')}>
      <h3 style={getStyle('sectionTitle')}>Skill Distribution</h3>
      <ResponsiveContainer width="100%" height="85%">
        <RadarChart data={mockData.skillDistribution}>
          <PolarGrid />
          <PolarAngleAxis dataKey="subject" />
          <PolarRadiusAxis domain={[0, 100]} />
          <Radar 
            name="Skills" 
            dataKey="score" 
            stroke="#667eea" 
            fill="#667eea" 
            fillOpacity={0.6} 
          />
          <Tooltip />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  </div>
);

// SWOT Analysis Component
const SWOTAnalysis = () => (
  <div style={{...getStyle('swotGrid'), ...getStyle('fullWidth')}}>
    <div style={{...getStyle('swotCard'), borderTopColor: '#4CAF50'}}>
      <h3 style={getStyle('swotTitle')}>
        <span>Strengths</span>
      </h3>
      <ul style={getStyle('swotList')}>
        {mockData.swotAnalysis.strengths.map((item, index) => (
          <li key={index} style={getStyle('swotItem')}>{item}</li>
        ))}
      </ul>
    </div>
    
    <div style={{...getStyle('swotCard'), borderTopColor: '#F44336'}}>
      <h3 style={getStyle('swotTitle')}>
        <span>Weaknesses</span>
      </h3>
      <ul style={getStyle('swotList')}>
        {mockData.swotAnalysis.weaknesses.map((item, index) => (
          <li key={index} style={getStyle('swotItem')}>{item}</li>
        ))}
      </ul>
    </div>
    
    <div style={{...getStyle('swotCard'), borderTopColor: '#2196F3'}}>
      <h3 style={getStyle('swotTitle')}>
        <span>Opportunities</span>
      </h3>
      <ul style={getStyle('swotList')}>
        {mockData.swotAnalysis.opportunities.map((item, index) => (
          <li key={index} style={getStyle('swotItem')}>{item}</li>
        ))}
      </ul>
    </div>
    
    <div style={{...getStyle('swotCard'), borderTopColor: '#FF9800'}}>
      <h3 style={getStyle('swotTitle')}>
        <span>Threats</span>
      </h3>
      <ul style={getStyle('swotList')}>
        {mockData.swotAnalysis.threats.map((item, index) => (
          <li key={index} style={getStyle('swotItem')}>{item}</li>
        ))}
      </ul>
    </div>
  </div>
);

// Interview History Component
const InterviewHistory = () => (
  <div style={{...getStyle('historyCard'), ...getStyle('fullWidth')}}>
    <h3 style={getStyle('sectionTitle')}>Interview History</h3>
    <table style={getStyle('historyTable')}>
      <thead style={getStyle('tableHeader')}>
        <tr>
          <th style={getStyle('tableHeaderCell')}>Date</th>
          <th style={getStyle('tableHeaderCell')}>Role</th>
          <th style={getStyle('tableHeaderCell')}>Score</th>
          <th style={getStyle('tableHeaderCell')}>Actions</th>
        </tr>
      </thead>
      <tbody>
        {mockData.interviewHistory.map(interview => (
          <tr key={interview.id} style={getStyle('tableRow')}>
            <td style={getStyle('tableCell')}>{interview.date}</td>
            <td style={getStyle('tableCell')}>{interview.role}</td>
            <td style={getStyle('tableCell')}>{interview.score}/100</td>
            <td style={getStyle('tableCell')}>
              <button style={getStyle('viewButton')}>View Details</button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

// Recommendations Component
const Recommendations = () => (
  <div style={{...getStyle('recommendationsCard'), ...getStyle('fullWidth')}}>
    <h3 style={getStyle('sectionTitle')}>AI Recommendations</h3>
    {mockData.recommendations.map((rec, index) => (
      <p key={index} style={getStyle('recommendationText')}>
        {rec}
      </p>
    ))}
  </div>
);

// Main Results Page Component
export default function ResultsPage() {
  const [activeTab, setActiveTab] = useState('overview');
  const [isMobile, setIsMobile] = useState(false);

  const renderContent = () => {
    switch (activeTab) {
      case 'skills':
        return <SkillsSection />;
      case 'history':
        return <InterviewHistory />;
      case 'swot':
        return <SWOTAnalysis />;
      default:
        return (
          <>
            <div style={getStyle('overviewGrid', isMobile)}>
              <ScoreCard score={mockData.overallScore} />
              <SkillsSection compact={true} />
            </div>
            <ChartsSection />
            <Recommendations />
          </>
        );
    }
  };

  return (
    <div style={getStyle('container')}>
      <Header candidate={mockData.candidate} />
      
      <TabNavigation activeTab={activeTab} onTabChange={setActiveTab} />
      
      <main style={getStyle('mainContent', isMobile)}>
        {renderContent()}
      </main>
    </div>
  );
}