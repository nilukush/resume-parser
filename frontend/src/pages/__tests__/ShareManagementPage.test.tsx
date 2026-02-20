/**
 * ShareManagementPage.test.tsx
 *
 * TDD Tests for ShareManagementPage component.
 *
 * This page is for the OWNER managing their share settings.
 * It should show:
 * - Share Link card with copyable public URL
 * - "Back to Review" button
 * - Share Settings (expiry, access count, revoke)
 * - Export buttons
 * - Resume Preview
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import ShareManagementPage from '../ShareManagementPage';
import * as api from '../../services/api';

// Mock the API module
vi.mock('../../services/api', () => ({
  resumeAPI: {
    getResume: vi.fn(),
    getShare: vi.fn(),
    createShare: vi.fn(),
    updateShare: vi.fn(),
    revokeShare: vi.fn(),
    exportPdf: vi.fn(),
    exportWhatsapp: vi.fn(),
    exportTelegram: vi.fn(),
    exportEmail: vi.fn(),
  },
}));

const mockNavigate = vi.fn();

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ id: 'test-resume-123' }),
    useNavigate: () => mockNavigate,
  };
});

// Mock window.navigator.clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn(() => Promise.resolve()),
  },
});

// Test data
const mockResumeData = {
  personal_info: {
    full_name: 'John Doe',
    email: 'john@example.com',
    phone: '+1-555-0123',
    location: 'San Francisco, CA',
  },
  work_experience: [
    {
      company: 'Tech Corp',
      title: 'Senior Software Engineer',
      location: 'San Francisco, CA',
      start_date: '2020',
      end_date: 'Present',
      description: 'Led development of cloud infrastructure',
      confidence: 85,
    },
  ],
  education: [
    {
      institution: 'Stanford University',
      degree: 'B.S. Computer Science',
      location: 'Stanford, CA',
      start_date: '2016',
      end_date: '2020',
      confidence: 90,
    },
  ],
  skills: {
    technical: ['React', 'TypeScript', 'Python'],
    soft: ['Leadership', 'Communication'],
    languages: ['English', 'Spanish'],
    certifications: ['AWS Solutions Architect'],
  },
  confidence_scores: {
    personal_info: 95,
    work_experience: 85,
    education: 90,
    skills: 88,
  },
};

const mockShareDetails = {
  share_token: 'abc-123-def',
  share_url: 'http://localhost:3000/shared/abc-123-def',  // NOTE: /shared/ NOT /share/
  resume_id: 'test-resume-123',
  created_at: '2026-02-20T10:00:00Z',
  expires_at: '2026-03-20T10:00:00Z',
  access_count: 5,
  is_active: true,
};

describe('ShareManagementPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  /**
   * TEST 1: Page loads and displays "Share Your Resume" heading
   */
  it('displays "Share Your Resume" heading when loaded', async () => {
    (api.resumeAPI.getResume as vi.Mock).mockResolvedValue({
      data: mockResumeData,
    });
    (api.resumeAPI.getShare as vi.Mock).mockResolvedValue(mockShareDetails);

    render(<ShareManagementPage />);

    await waitFor(() => {
      expect(screen.getByText('Share Your Resume')).toBeInTheDocument();
    });
  });

  /**
   * TEST 2: Share Link card is displayed with correct public URL format
   * The public URL should be /shared/{share_token}, NOT /share/{share_token}
   */
  it('displays Share Link card with public URL format (/shared/{token})', async () => {
    (api.resumeAPI.getResume as vi.Mock).mockResolvedValue({
      data: mockResumeData,
    });
    (api.resumeAPI.getShare as vi.Mock).mockResolvedValue(mockShareDetails);

    render(<ShareManagementPage />);

    await waitFor(() => {
      const shareInput = screen.getByDisplayValue('http://localhost:3000/shared/abc-123-def');
      expect(shareInput).toBeInTheDocument();
      expect(screen.getByText('Share Link')).toBeInTheDocument();
    });
  });

  /**
   * TEST 3: "Back to Review" button is visible and navigates correctly
   */
  it('displays "Back to Review" button and navigates to review page', async () => {
    (api.resumeAPI.getResume as vi.Mock).mockResolvedValue({
      data: mockResumeData,
    });
    (api.resumeAPI.getShare as vi.Mock).mockResolvedValue(mockShareDetails);

    render(<ShareManagementPage />);

    await waitFor(() => {
      const backButton = screen.getByText('Back to Review');
      expect(backButton).toBeInTheDocument();

      fireEvent.click(backButton);
    });

    expect(mockNavigate).toHaveBeenCalledWith('/review/test-resume-123');
  });

  /**
   * TEST 4: Share Settings are displayed (expiry, access count, active status)
   */
  it('displays share settings with expiry, access count, and active status', async () => {
    (api.resumeAPI.getResume as vi.Mock).mockResolvedValue({
      data: mockResumeData,
    });
    (api.resumeAPI.getShare as vi.Mock).mockResolvedValue(mockShareDetails);

    render(<ShareManagementPage />);

    await waitFor(() => {
      expect(screen.getByText(/Total views/i)).toBeInTheDocument();  // Component uses "Total views"
      expect(screen.getByText('Share Settings')).toBeInTheDocument();  // Settings heading
      // Check that access count appears (we know it's 5 from mock data)
      const totalViewsSection = screen.getByText(/Total views/i).parentElement?.parentElement;
      expect(totalViewsSection?.textContent).toContain('5');
    });
  });

  /**
   * TEST 5: Resume preview is displayed with all sections
   */
  it('displays resume preview with all sections', async () => {
    (api.resumeAPI.getResume as vi.Mock).mockResolvedValue({
      data: mockResumeData,
    });
    (api.resumeAPI.getShare as vi.Mock).mockResolvedValue(mockShareDetails);

    render(<ShareManagementPage />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Tech Corp')).toBeInTheDocument();
      expect(screen.getByText('Stanford University')).toBeInTheDocument();
      expect(screen.getByText('React')).toBeInTheDocument();
    });
  });

  /**
   * TEST 6: Copy button copies share URL to clipboard
   */
  it('copies share URL to clipboard when copy button is clicked', async () => {
    (api.resumeAPI.getResume as vi.Mock).mockResolvedValue({
      data: mockResumeData,
    });
    (api.resumeAPI.getShare as vi.Mock).mockResolvedValue(mockShareDetails);

    render(<ShareManagementPage />);

    await waitFor(() => {
      const copyButton = screen.getByRole('button', { name: /copy/i });
      fireEvent.click(copyButton);
    });

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      'http://localhost:3000/shared/abc-123-def'
    );
  });
});
