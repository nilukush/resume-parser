export interface PersonalInfo {
  full_name: string
  email: string
  phone: string
  location: string
  linkedin_url: string
  github_url: string
  portfolio_url: string
  summary: string
}

export interface WorkExperience {
  company: string
  title: string
  location: string
  start_date: string
  end_date: string
  description: string
  confidence: number
}

export interface Education {
  institution: string
  degree: string
  field_of_study: string
  location: string
  start_date: string
  end_date: string
  gpa: string
  confidence: number
}

export interface Skills {
  technical: string[]
  soft_skills: string[]
  languages: string[]
  certifications: string[]
  confidence: number
}

export interface ConfidenceScores {
  personal_info: number
  work_experience: number
  education: number
  skills: number
}

export interface ParsedResumeData {
  id: string
  status: string
  confidence_score: number
  personal_info: PersonalInfo
  work_experience: WorkExperience[]
  education: Education[]
  skills: Skills
  confidence_scores: ConfidenceScores
}
