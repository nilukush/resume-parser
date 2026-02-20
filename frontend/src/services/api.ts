/**
 * API service for ResuMate backend communication.
 *
 * This module provides functions to interact with the backend API
 * for resume operations (upload, retrieve, update).
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/v1';

/**
 * Resume data types matching backend structure
 */
export interface PersonalInfo {
  full_name: string;
  email: string;
  phone: string;
  location: string;
  linkedin_url: string;
  github_url: string;
  portfolio_url: string;
  summary: string;
}

export interface WorkExperience {
  company: string;
  title: string;
  location: string;
  start_date: string;
  end_date: string;
  description: string;
  confidence: number;
}

export interface Education {
  institution: string;
  degree: string;
  field_of_study: string;
  location: string;
  start_date: string;
  end_date: string;
  gpa: string;
  confidence: number;
}

export interface Skills {
  technical: string[];
  soft: string[];
  languages: (string | { language: string; proficiency: string })[];
  certifications: string[];
  confidence?: number;
}

export interface ConfidenceScores {
  personal_info: number;
  work_experience: number;
  education: number;
  skills: number;
}

export interface ParsedResumeData {
  personal_info: PersonalInfo;
  work_experience: WorkExperience[];
  education: Education[];
  skills: Skills;
  confidence_scores: ConfidenceScores;
}

export interface ResumeResponse {
  resume_id: string;
  status: string;
  data: ParsedResumeData | null;
  message?: string;
}

export interface PublicResumeData {
  resume_id: string;
  personal_info: PersonalInfo;
  work_experience: WorkExperience[];
  education: Education[];
  skills: Skills;
  confidence_scores: ConfidenceScores;
}

export interface ResumeUpdateRequest {
  personal_info?: Partial<PersonalInfo>;
  work_experience?: WorkExperience[];
  education?: Education[];
  skills?: Partial<Skills>;
}

/**
 * Share-related types
 */
export interface ShareData {
  share_token: string;
  share_url: string;
  expires_at: string;
}

export interface ShareDetails {
  share_token: string;
  share_url: string;
  resume_id: string;
  created_at: string;
  expires_at: string;
  access_count: number;
  is_active: boolean;
}

export interface ExportResponse {
  whatsapp_url?: string;
  telegram_url?: string;
  mailto_url?: string;
}

/**
 * API class for backend communication
 */
export class ResumeAPI {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Fetch parsed resume data by ID
   */
  async getResume(resumeId: string): Promise<ResumeResponse> {
    const response = await fetch(`${this.baseUrl}/resumes/${resumeId}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Resume not found or still processing');
      }
      throw new Error(`Failed to fetch resume: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Update parsed resume data with corrections
   */
  async updateResume(
    resumeId: string,
    updateData: ResumeUpdateRequest
  ): Promise<ResumeResponse> {
    const response = await fetch(`${this.baseUrl}/resumes/${resumeId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updateData),
    });

    if (!response.ok) {
      throw new Error(`Failed to update resume: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Upload a resume file for parsing
   */
  async uploadResume(file: File): Promise<{ resume_id: string; websocket_url: string }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/resumes/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to upload resume');
    }

    const data = await response.json();
    return {
      resume_id: data.resume_id,
      websocket_url: data.websocket_url,
    };
  }

  /**
   * Create a shareable link for a resume
   */
  async createShare(resumeId: string): Promise<ShareData> {
    const response = await fetch(`${this.baseUrl}/resumes/${resumeId}/share`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to create share: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get share details for a resume
   */
  async getShare(resumeId: string): Promise<ShareDetails> {
    const response = await fetch(`${this.baseUrl}/resumes/${resumeId}/share`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Share not found. Please create a share link first.');
      }
      throw new Error(`Failed to get share: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get public shared resume by share token
   */
  async getPublicShare(shareToken: string): Promise<{
    resume_id: string;
    personal_info: PersonalInfo;
    work_experience: WorkExperience[];
    education: Education[];
    skills: Skills;
    confidence_scores: ConfidenceScores;
  }> {
    const response = await fetch(`${this.baseUrl}/share/${shareToken}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Share not found or has been revoked.');
      }
      if (response.status === 410) {
        throw new Error('This share link has expired.');
      }
      if (response.status === 403) {
        throw new Error('This share has been revoked.');
      }
      throw new Error(`Failed to get shared resume: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Revoke a shareable link for a resume
   */
  async revokeShare(resumeId: string): Promise<{ message: string; resume_id: string }> {
    const response = await fetch(`${this.baseUrl}/resumes/${resumeId}/share`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to revoke share: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Export resume as PDF
   */
  async exportPdf(resumeId: string): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/resumes/${resumeId}/export/pdf`);

    if (!response.ok) {
      throw new Error(`Failed to export PDF: ${response.statusText}`);
    }

    return response.blob();
  }

  /**
   * Get WhatsApp share link
   */
  async exportWhatsapp(resumeId: string): Promise<ExportResponse> {
    const response = await fetch(`${this.baseUrl}/resumes/${resumeId}/export/whatsapp`);

    if (!response.ok) {
      throw new Error(`Failed to get WhatsApp link: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get Telegram share link
   */
  async exportTelegram(resumeId: string): Promise<ExportResponse> {
    const response = await fetch(`${this.baseUrl}/resumes/${resumeId}/export/telegram`);

    if (!response.ok) {
      throw new Error(`Failed to get Telegram link: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get email mailto link
   */
  async exportEmail(resumeId: string): Promise<ExportResponse> {
    const response = await fetch(`${this.baseUrl}/resumes/${resumeId}/export/email`);

    if (!response.ok) {
      throw new Error(`Failed to get email link: ${response.statusText}`);
    }

    return response.json();
  }
}

// Export singleton instance
export const resumeAPI = new ResumeAPI();
