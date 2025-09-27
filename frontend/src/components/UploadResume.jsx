// pages/upload.js
import { useState, useRef } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';

export default function UploadResume() {
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const fileInputRef = useRef(null);
  const router = useRouter();

  // Mock AI analysis results
  const mockAnalysis = {
    score: 76,
    strengths: [
      'Strong technical skills in React and JavaScript',
      'Excellent project experience with modern frameworks',
      'Good educational background',
      'Clear career progression'
    ],
    weaknesses: [
      'Limited leadership experience',
      'Could benefit from more certifications',
      'Gap in employment history needs explanation'
    ],
    recommendations: [
      'Add more quantifiable achievements',
      'Include specific project metrics',
      'Highlight leadership experiences',
      'Update with recent technologies'
    ],
    suggestedRoles: ['Frontend Developer', 'React Developer', 'UI Engineer'],
    compatibility: 82
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === 'application/pdf') {
      processFile(droppedFile);
    } else {
      alert('Please upload a PDF file');
    }
  };

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      processFile(selectedFile);
    }
  };

  const processFile = (file) => {
    setFile(file);
    setAnalysisResult(null);
    simulateUploadAndAnalysis(file);
  };

  const simulateUploadAndAnalysis = async (file) => {
    setIsUploading(true);
    setUploadProgress(0);
    setAnalysisProgress(0);

    // Simulate upload progress
    for (let i = 0; i <= 100; i += 10) {
      await new Promise(resolve => setTimeout(resolve, 200));
      setUploadProgress(i);
    }

    // Simulate analysis progress
    for (let i = 0; i <= 100; i += 5) {
      await new Promise(resolve => setTimeout(resolve, 150));
      setAnalysisProgress(i);
    }

    setIsUploading(false);
    setAnalysisResult(mockAnalysis);
  };

  const handleRetry = () => {
    setFile(null);
    setAnalysisResult(null);
    setUploadProgress(0);
    setAnalysisProgress(0);
  };

  const handleViewResults = () => {
    router.push('/results');
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <>
      <Head>
        <title>Upload Resume - CodeSage AI</title>
        <meta name="description" content="Upload your resume for AI analysis" />
      </Head>

      <div style={styles.container}>
        <div style={styles.header}>
          <h1 style={styles.title}>AI Resume Analysis</h1>
          <p style={styles.subtitle}>
            Upload your resume and get instant AI-powered feedback to improve your job prospects
          </p>
        </div>

        <div style={styles.content}>
          {!file && !analysisResult && (
            <div 
              style={{
                ...styles.uploadZone,
                ...(isDragging ? styles.uploadZoneDragging : {}),
                animation: 'fadeInUp 0.6s ease-out'
              }}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <div style={styles.uploadIcon}>
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" strokeWidth="2"/>
                  <polyline points="14,2 14,8 20,8" stroke="currentColor" strokeWidth="2"/>
                  <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" strokeWidth="2"/>
                  <line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" strokeWidth="2"/>
                  <polyline points="10,9 9,9 8,9" stroke="currentColor" strokeWidth="2"/>
                </svg>
              </div>
              <h3 style={styles.uploadTitle}>Drop your resume here</h3>
              <p style={styles.uploadText}>or click to browse files</p>
              <p style={styles.uploadHint}>Supports PDF files up to 5MB</p>
              
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handleFileSelect}
                style={styles.fileInput}
              />
            </div>
          )}

          {file && isUploading && (
            <div style={styles.progressContainer}>
              <div style={styles.progressCard}>
                <h3 style={styles.progressTitle}>Analyzing Your Resume</h3>
                
                <div style={styles.fileInfo}>
                  <div style={styles.fileIcon}>📄</div>
                  <div style={styles.fileDetails}>
                    <p style={styles.fileName}>{file.name}</p>
                    <p style={styles.fileSize}>{formatFileSize(file.size)}</p>
                  </div>
                </div>

                <div style={styles.progressSection}>
                  <div style={styles.progressHeader}>
                    <span>Uploading</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div style={styles.progressBar}>
                    <div 
                      style={{
                        ...styles.progressFill,
                        width: `${uploadProgress}%`,
                        background: 'linear-gradient(90deg, #667eea, #764ba2)'
                      }} 
                    />
                  </div>
                </div>

                <div style={styles.progressSection}>
                  <div style={styles.progressHeader}>
                    <span>AI Analysis</span>
                    <span>{analysisProgress}%</span>
                  </div>
                  <div style={styles.progressBar}>
                    <div 
                      style={{
                        ...styles.progressFill,
                        width: `${analysisProgress}%`,
                        background: 'linear-gradient(90deg, #ff6b6b, #feca57)'
                      }} 
                    />
                  </div>
                </div>

                <div style={styles.analyzingAnimation}>
                  <div style={styles.pulseDot}></div>
                  <span style={styles.analyzingText}>AI is analyzing your resume...</span>
                </div>
              </div>
            </div>
          )}

          {analysisResult && (
            <div style={styles.resultContainer}>
              <div style={styles.resultHeader}>
                <h2 style={styles.resultTitle}>Analysis Complete!</h2>
                <p style={styles.resultSubtitle}>Here's what our AI found</p>
              </div>

              <div style={styles.scoreCard}>
                <div style={styles.scoreCircle}>
                  <div style={styles.scoreValue}>{analysisResult.score}</div>
                  <div style={styles.scoreLabel}>Overall Score</div>
                </div>
                <div style={styles.compatibility}>
                  <span>Job Match: {analysisResult.compatibility}%</span>
                  <div style={styles.compatibilityBar}>
                    <div style={{...styles.compatibilityFill, width: `${analysisResult.compatibility}%`}}></div>
                  </div>
                </div>
              </div>

              <div style={styles.analysisGrid}>
                <div style={styles.analysisCard}>
                  <h4 style={styles.cardTitle}>💪 Strengths</h4>
                  <ul style={styles.list}>
                    {analysisResult.strengths.map((strength, index) => (
                      <li key={index} style={styles.listItem}>{strength}</li>
                    ))}
                  </ul>
                </div>

                <div style={styles.analysisCard}>
                  <h4 style={styles.cardTitle}>📋 Recommendations</h4>
                  <ul style={styles.list}>
                    {analysisResult.recommendations.map((rec, index) => (
                      <li key={index} style={styles.listItem}>{rec}</li>
                    ))}
                  </ul>
                </div>

                <div style={styles.analysisCard}>
                  <h4 style={styles.cardTitle}>🎯 Suggested Roles</h4>
                  <div style={styles.rolesContainer}>
                    {analysisResult.suggestedRoles.map((role, index) => (
                      <span key={index} style={styles.roleTag}>{role}</span>
                    ))}
                  </div>
                </div>

                <div style={styles.analysisCard}>
                  <h4 style={styles.cardTitle}>📈 Areas to Improve</h4>
                  <ul style={styles.list}>
                    {analysisResult.weaknesses.map((weakness, index) => (
                      <li key={index} style={styles.listItem}>{weakness}</li>
                    ))}
                  </ul>
                </div>
              </div>

              <div style={styles.actionButtons}>
                <button 
                  style={styles.secondaryButton}
                  onClick={handleRetry}
                >
                  Analyze Another Resume
                </button>
                <button 
                  style={styles.primaryButton}
                  onClick={handleViewResults}
                >
                  View Detailed Results
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <style jsx global>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes pulse {
          0% { transform: scale(1); }
          50% { transform: scale(1.05); }
          100% { transform: scale(1); }
        }
        
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateX(-20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        
        @keyframes progressFill {
          from { width: 0%; }
        }
      `}</style>
    </>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    padding: '20px',
  },
  header: {
    textAlign: 'center',
    marginBottom: '40px',
    color: 'white',
  },
  title: {
    fontSize: '3rem',
    fontWeight: '700',
    margin: '0 0 10px 0',
    background: 'linear-gradient(45deg, #fff, #f0f0f0)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  subtitle: {
    fontSize: '1.2rem',
    opacity: '0.9',
    maxWidth: '600px',
    margin: '0 auto',
    lineHeight: '1.6',
  },
  content: {
    maxWidth: '800px',
    margin: '0 auto',
  },
  uploadZone: {
    background: 'rgba(255, 255, 255, 0.95)',
    backdropFilter: 'blur(10px)',
    border: '3px dashed rgba(102, 126, 234, 0.3)',
    borderRadius: '20px',
    padding: '60px 40px',
    textAlign: 'center',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    animation: 'fadeInUp 0.6s ease-out',
  },
  uploadZoneDragging: {
    borderColor: '#667eea',
    background: 'rgba(102, 126, 234, 0.1)',
    transform: 'scale(1.02)',
  },
  uploadIcon: {
    color: '#667eea',
    marginBottom: '20px',
  },
  uploadTitle: {
    fontSize: '1.5rem',
    fontWeight: '600',
    margin: '0 0 10px 0',
    color: '#333',
  },
  uploadText: {
    fontSize: '1.1rem',
    color: '#666',
    margin: '0 0 5px 0',
  },
  uploadHint: {
    fontSize: '0.9rem',
    color: '#999',
    margin: '0',
  },
  fileInput: {
    display: 'none',
  },
  progressContainer: {
    animation: 'fadeInUp 0.6s ease-out',
  },
  progressCard: {
    background: 'rgba(255, 255, 255, 0.95)',
    backdropFilter: 'blur(10px)',
    borderRadius: '20px',
    padding: '40px',
    textAlign: 'center',
  },
  progressTitle: {
    fontSize: '1.5rem',
    fontWeight: '600',
    margin: '0 0 30px 0',
    color: '#333',
  },
  fileInfo: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '15px',
    marginBottom: '30px',
  },
  fileIcon: {
    fontSize: '2rem',
  },
  fileDetails: {
    textAlign: 'left',
  },
  fileName: {
    margin: '0',
    fontWeight: '600',
    color: '#333',
  },
  fileSize: {
    margin: '5px 0 0 0',
    color: '#666',
    fontSize: '0.9rem',
  },
  progressSection: {
    marginBottom: '25px',
  },
  progressHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '10px',
    fontSize: '0.9rem',
    color: '#666',
  },
  progressBar: {
    height: '8px',
    background: '#f0f0f0',
    borderRadius: '4px',
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: '4px',
    transition: 'width 0.3s ease',
    animation: 'progressFill 1s ease-out',
  },
  analyzingAnimation: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '10px',
    marginTop: '30px',
  },
  pulseDot: {
    width: '12px',
    height: '12px',
    background: 'linear-gradient(45deg, #ff6b6b, #feca57)',
    borderRadius: '50%',
    animation: 'pulse 1.5s infinite',
  },
  analyzingText: {
    color: '#666',
    fontSize: '0.9rem',
  },
  resultContainer: {
    animation: 'fadeInUp 0.6s ease-out',
  },
  resultHeader: {
    textAlign: 'center',
    marginBottom: '40px',
    color: 'white',
  },
  resultTitle: {
    fontSize: '2.5rem',
    fontWeight: '700',
    margin: '0 0 10px 0',
  },
  resultSubtitle: {
    fontSize: '1.1rem',
    opacity: '0.9',
  },
  scoreCard: {
    background: 'rgba(255, 255, 255, 0.95)',
    backdropFilter: 'blur(10px)',
    borderRadius: '20px',
    padding: '30px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-around',
    marginBottom: '30px',
  },
  scoreCircle: {
    textAlign: 'center',
  },
  scoreValue: {
    fontSize: '3rem',
    fontWeight: '700',
    background: 'linear-gradient(135deg, #667eea, #764ba2)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    margin: '0',
  },
  scoreLabel: {
    color: '#666',
    fontSize: '1rem',
    margin: '5px 0 0 0',
  },
  compatibility: {
    textAlign: 'center',
  },
  compatibilityBar: {
    width: '200px',
    height: '8px',
    background: '#f0f0f0',
    borderRadius: '4px',
    marginTop: '10px',
    overflow: 'hidden',
  },
  compatibilityFill: {
    height: '100%',
    background: 'linear-gradient(90deg, #4CAF50, #8BC34A)',
    borderRadius: '4px',
    transition: 'width 0.5s ease',
  },
  analysisGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '20px',
    marginBottom: '40px',
  },
  analysisCard: {
    background: 'rgba(255, 255, 255, 0.95)',
    backdropFilter: 'blur(10px)',
    borderRadius: '15px',
    padding: '25px',
    animation: 'slideIn 0.6s ease-out',
  },
  cardTitle: {
    fontSize: '1.2rem',
    fontWeight: '600',
    margin: '0 0 15px 0',
    color: '#333',
  },
  list: {
    margin: '0',
    paddingLeft: '20px',
  },
  listItem: {
    marginBottom: '8px',
    color: '#555',
    lineHeight: '1.5',
  },
  rolesContainer: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '10px',
  },
  roleTag: {
    background: 'linear-gradient(135deg, #667eea, #764ba2)',
    color: 'white',
    padding: '5px 12px',
    borderRadius: '20px',
    fontSize: '0.9rem',
    fontWeight: '500',
  },
  actionButtons: {
    display: 'flex',
    gap: '15px',
    justifyContent: 'center',
  },
  primaryButton: {
    background: 'linear-gradient(135deg, #667eea, #764ba2)',
    color: 'white',
    border: 'none',
    padding: '12px 30px',
    borderRadius: '10px',
    fontSize: '1rem',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
  },
  secondaryButton: {
    background: 'rgba(255, 255, 255, 0.2)',
    color: 'white',
    border: '2px solid rgba(255, 255, 255, 0.3)',
    padding: '12px 30px',
    borderRadius: '10px',
    fontSize: '1rem',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
  },
};

// Add hover effects
styles.uploadZone[':hover'] = {
  borderColor: '#667eea',
  transform: 'translateY(-2px)',
  boxShadow: '0 10px 30px rgba(102, 126, 234, 0.2)',
};

styles.primaryButton[':hover'] = {
  transform: 'translateY(-2px)',
  boxShadow: '0 5px 15px rgba(102, 126, 234, 0.4)',
};

styles.secondaryButton[':hover'] = {
  background: 'rgba(255, 255, 255, 0.3)',
  transform: 'translateY(-2px)',
};

export default UploadResume;