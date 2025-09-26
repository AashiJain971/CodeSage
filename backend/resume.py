"""Module for handling resume processing in the AI Interview System."""
import PyPDF2
import docx
import re
from typing import Dict, List, Optional
from pathlib import Path

class ResumeProcessor:
    """Class to handle resume processing and skill extraction."""

    def __init__(self):
        # Common skills and keywords to look for in resumes
        self.skill_categories = {
            "programming_languages": [
                "python", "java", "javascript", "c++", "c#", "ruby", "php", "swift",
                "kotlin", "golang", "rust", "typescript", "scala", "r", "matlab"
            ],
            "web_technologies": [
                "html", "css", "react", "angular", "vue", "node.js", "express",
                "django", "flask", "spring", "asp.net", "php", "laravel", "ruby on rails"
            ],
            "databases": [
                "sql", "mysql", "postgresql", "mongodb", "oracle", "sqlite",
                "redis", "cassandra", "elasticsearch", "dynamodb", "mariadb"
            ],
            "cloud_platforms": [
                "aws", "azure", "google cloud", "gcp", "heroku", "digitalocean",
                "kubernetes", "docker", "terraform", "cloudformation"
            ],
            "tools_and_frameworks": [
                "git", "jenkins", "jira", "confluence", "webpack", "babel",
                "maven", "gradle", "npm", "yarn", "docker", "kubernetes"
            ],
            "soft_skills": [
                "leadership", "communication", "teamwork", "problem solving",
                "project management", "time management", "analytical", "creativity"
            ],
            "data_science": [
                "machine learning", "deep learning", "ai", "artificial intelligence",
                "data analysis", "statistics", "pandas", "numpy", "scikit-learn",
                "tensorflow", "pytorch", "nlp", "computer vision"
            ],
            "mobile_development": [
                "android", "ios", "swift", "kotlin", "react native", "flutter",
                "xamarin", "mobile app development", "app development"
            ],
            "devops": [
                "ci/cd", "jenkins", "docker", "kubernetes", "terraform", "ansible",
                "puppet", "chef", "aws", "azure", "devops", "sre"
            ]
        }

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from a PDF file."""
        try:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error reading PDF resume: {e}")
            return ""

    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from a DOCX file."""
        try:
            doc = docx.Document(file_path)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except Exception as e:
            print(f"Error reading DOCX resume: {e}")
            return ""

    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from a TXT file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading TXT resume: {e}")
            return ""

    def extract_resume_text(self, file_path: str) -> Optional[str]:
        """Extract text from a resume file (PDF, DOCX, or TXT)."""
        if not file_path:
            return None

        file_path = str(file_path)  # Convert Path to string if needed
        
        if file_path.lower().endswith('.pdf'):
            text = self.extract_text_from_pdf(file_path)
        elif file_path.lower().endswith('.docx'):
            text = self.extract_text_from_docx(file_path)
        elif file_path.lower().endswith('.txt'):
            text = self.extract_text_from_txt(file_path)
        else:
            print("Unsupported resume format. Please upload PDF, DOCX, or TXT.")
            return None

        return text.strip() if text else None

    def extract_skills(self, resume_text: str) -> Dict[str, List[str]]:
        """Extract skills from resume text by category."""
        if not resume_text:
            return {}

        resume_text = resume_text.lower()
        found_skills = {}

        for category, skills in self.skill_categories.items():
            found_skills[category] = []
            for skill in skills:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, resume_text):
                    found_skills[category].append(skill)

        # Remove empty categories
        return {k: v for k, v in found_skills.items() if v}

    def extract_experience(self, resume_text: str) -> List[Dict[str, str]]:
        """Extract work experience sections from resume text."""
        if not resume_text:
            return []

        experience = []
        # Common section headers that indicate work experience
        experience_headers = [
            "work experience",
            "professional experience",
            "employment history",
            "work history"
        ]

        text_lower = resume_text.lower()
        for header in experience_headers:
            if header in text_lower:
                # Simple regex to find content between experience headers and the next section
                pattern = f"{header}.*?(?=education|skills|projects|references|$)"
                matches = re.findall(pattern, text_lower, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    experience.append({
                        "section": header,
                        "content": match.strip()
                    })

        return experience

    def extract_education(self, resume_text: str) -> List[Dict[str, str]]:
        """Extract education sections from resume text."""
        if not resume_text:
            return []

        education = []
        education_headers = [
            "education",
            "academic background",
            "academic qualifications",
            "qualifications"
        ]

        text_lower = resume_text.lower()
        for header in education_headers:
            if header in text_lower:
                pattern = f"{header}.*?(?=experience|skills|projects|references|$)"
                matches = re.findall(pattern, text_lower, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    education.append({
                        "section": header,
                        "content": match.strip()
                    })

        return education

    def analyze_resume(self, file_path: str) -> Dict[str, any]:
        """
        Analyze a resume and extract relevant information.
        
        Returns a dictionary containing:
        - resume_text: The full text of the resume
        - skills: Dictionary of skills by category
        - experience: List of work experience sections
        - education: List of education sections
        """
        resume_text = self.extract_resume_text(file_path)
        if not resume_text:
            return {"error": "Failed to extract text from resume"}

        return {
            "resume_text": resume_text,
            "skills": self.extract_skills(resume_text),
            "experience": self.extract_experience(resume_text),
            "education": self.extract_education(resume_text)
        }

    def generate_interview_recommendations(self, resume_analysis: Dict[str, any]) -> List[str]:
        """
        Generate interview question recommendations based on resume analysis.
        """
        recommendations = []
        
        # Add skills-based questions
        if "skills" in resume_analysis:
            for category, skills in resume_analysis["skills"].items():
                if skills:
                    if category == "programming_languages":
                        recommendations.append(f"Ask about experience with {', '.join(skills)} programming")
                    elif category == "web_technologies":
                        recommendations.append(f"Discuss projects using {', '.join(skills)}")
                    elif category == "databases":
                        recommendations.append(f"Explore database experience with {', '.join(skills)}")
                    elif category == "cloud_platforms":
                        recommendations.append(f"Ask about cloud architecture using {', '.join(skills)}")

        # Add experience-based questions
        if "experience" in resume_analysis:
            for exp in resume_analysis["experience"]:
                recommendations.append("Ask about specific achievements and challenges in previous roles")
                recommendations.append("Discuss project management and team collaboration experiences")

        # Add education-based questions
        if "education" in resume_analysis:
            recommendations.append("Ask about relevant coursework and academic projects")
            recommendations.append("Discuss application of academic knowledge in practical scenarios")

        return recommendations

def create_resume_upload_endpoint():
    """
    Returns FastAPI endpoint code for resume upload functionality.
    This is a helper function to show how to integrate with FastAPI.
    """
    return """
from fastapi import FastAPI, UploadFile, File
from pathlib import Path
import shutil
from .resume import ResumeProcessor

@app.post("/resume/upload")
async def upload_resume(resume: UploadFile = File(...)):
    try:
        # Create a temporary file to store the uploaded resume
        temp_file = Path(f"temp_{resume.filename}")
        with temp_file.open("wb") as buffer:
            shutil.copyfileobj(resume.file, buffer)
        
        # Process the resume
        processor = ResumeProcessor()
        analysis = processor.analyze_resume(str(temp_file))
        
        # Clean up the temporary file
        temp_file.unlink()
        
        if "error" in analysis:
            return {"status": "error", "message": analysis["error"]}
            
        return {
            "status": "success",
            "resume_text": analysis["resume_text"],
            "skills": analysis["skills"],
            "interview_recommendations": processor.generate_interview_recommendations(analysis)
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
    """