/**
 * PublicSharedResumePage.test.tsx
 *
 * TDD Tests for PublicSharedResumePage component.
 *
 * This page is for PUBLIC viewers accessing a shared resume link.
 * It should show:
 * - Read-only resume data
 * - Export buttons (PDF, WhatsApp, Telegram, Email)
 * - NO "Back to Review" button (public view)
 * - NO share settings (public view)
 * - NO edit capabilities (public view)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import PublicSharedResumePage from '../PublicSharedResumePage';
import * as api from '../../services/api';

// Mock the API module
vi.mock('../../services/api', () => ({
  resumeAPI: {
    getPublicShare: vi.fn(),
    exportPdf: vi.fn(),
    exportWhatsapp: vi.fn(),
    exportTelegram: vi.fn(),
    exportEmail: vi.fn(),
  },
}));

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ token: 'test-share-token-abc123' }),
    useNavigate: () => vi.fn(),
  };
});

// Mock window.open for export links
const mockOpen = vi.fn();
Object.assign(window, { open: mockOpen });

// Test data
const mockPublicResumeData = {
  resume_id: 'test-resume-123',
  personal_info: {
    full_name: 'John Doe',
    email: 'john@example.com',
    phone: '+1-555-0123',
    location: 'San Francisco, CA',
    linkedin_url: 'https://linkedin.com/in/johndoe',
    portfolio_url: 'https://johndoe.com',
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
    technical: ['React', 'TypeScript', 'Python', 'AWS'],
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

describe('PublicSharedResumePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  /**
   * TEST 1: Page displays resume data when loaded
   */
  it('displays "Shared Resume" heading', async () => {
    vi.mocked(api.resumeAPI.getPublicShare).mockResolvedValue(mockPublicResumeData);

    render(<PublicSharedResumePage />);

    await waitFor(() => {
      expect(screen.getByText('Shared Resume')).toBeInTheDocument();
    });
  });

  /**
   * TEST 2: Personal Information section is displayed
   */
  it('displays personal information section', async () => {
    vi.mocked(api.resumeAPI.getPublicShare).mockResolvedValue(mockPublicResumeData);

    render(<PublicSharedResumePage />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('john@example.com')).toBeInTheDocument();
      expect(screen.getByText('+1-555-0123')).toBeInTheDocument();
      expect(screen.getByText('San Francisco, CA')).toBeInTheDocument();
    });
  });

  /**
   * TEST 3: Work Experience section is displayed
   */
  it('displays work experience section', async () => {
    vi.mocked(api.resumeAPI.getPublicShare).mockResolvedValue(mockPublicResumeData);

    render(<PublicSharedResumePage />);

    await waitFor(() => {
      expect(screen.getByText('Work Experience')).toBeInTheDocument();
      expect(screen.getByText('Tech Corp')).toBeInTheDocument();
      expect(screen.getByText('Senior Software Engineer')).toBeInTheDocument();
    });
  });

  /**
   * TEST 4: Education section is displayed
   */
  it('displays education section', async () => {
    vi.mocked(api.resumeAPI.getPublicShare).mockResolvedValue(mockPublicResumeData);

    render(<PublicSharedResumePage />);

    await waitFor(() => {
      expect(screen.getByText('Education')).toBeInTheDocument();
      expect(screen.getByText('Stanford University')).toBeInTheDocument();
      expect(screen.getByText('B.S. Computer Science')).toBeInTheDocument();
    });
  });

  /**
   * TEST 5: Skills section is displayed with categories
   */
  it('displays skills section with categories', async () => {
    vi.mocked(api.resumeAPI.getPublicShare).mockResolvedValue(mockPublicResumeData);

    render(<PublicSharedResumePage />);

    await waitFor(() => {
      expect(screen.getByText('Skills')).toBeInTheDocument();
      expect(screen.getByText('React')).toBeInTheDocument();
      expect(screen.getByText('TypeScript')).toBeInTheDocument();
      expect(screen.getByText('Leadership')).toBeInTheDocument();
    });
  });

  /**
   * TEST 6: Export buttons are visible and functional
   */
  it('displays export buttons and handles clicks', async () => {
    vi.mocked(api.resumeAPI.getPublicShare).mockResolvedValue(mockPublicResumeData);

    // Mock export URLs
    vi.mocked(api.resumeAPI.exportPdf).mockResolvedValue(new Blob());
    vi.mocked(api.resumeAPI.exportWhatsapp).mockResolvedValue({
      whatsapp_url: 'https://wa.me/?text=Test',
    });
    vi.mocked(api.resumeAPI.exportTelegram).mockResolvedValue({
      telegram_url: 'https://t.me/share/url?url=&text=Test',
    });
    vi.mocked(api.resumeAPI.exportEmail).mockResolvedValue({
      mailto_url: 'mailto:?subject=Test&body=Test',
    });

    render(<PublicSharedResumePage />);

    await waitFor(() => {
      expect(screen.getByText('Export as PDF')).toBeInTheDocument();
      expect(screen.getByText('Share via WhatsApp')).toBeInTheDocument();
      expect(screen.getByText('Share via Telegram')).toBeInTheDocument();
      expect(screen.getByText('Share via Email')).toBeInTheDocument();
    });

    // Test PDF export button
    const pdfButton = screen.getByText('Export as PDF');
    await fireEvent.click(pdfButton);
    await waitFor(() => {
      expect(api.resumeAPI.exportPdf).toHaveBeenCalledWith('test-resume-123');
    });
  });

  /**
   * TEST 7: Loading state is displayed
   */
  it('displays loading state initially', () => {
    vi.mocked(api.resumeAPI.getPublicShare).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<PublicSharedResumePage />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  /**
   * TEST 8: Error state is displayed on API failure
   */
  it('displays error state when API call fails', async () => {
    vi.mocked(api.resumeAPI.getPublicShare).mockRejectedValue(
      new Error('Share not found')
    );

    render(<PublicSharedResumePage />);

    await waitFor(() => {
      expect(
        screen.getByText(/failed to load shared resume/i)
      ).toBeInTheDocument();
    });
  });

  /**
   * TEST 9: Does NOT display "Back to Review" button (public view)
   */
  it('does not display "Back to Review" button in public view', async () => {
    vi.mocked(api.resumeAPI.getPublicShare).mockResolvedValue(mockPublicResumeData);

    render(<PublicSharedResumePage />);

    await waitFor(() => {
      expect(screen.queryByText('Back to Review')).not.toBeInTheDocument();
    });
  });

  /**
   * TEST 10: Does NOT display share settings (public view)
   */
  it('does not display share settings in public view', async () => {
    vi.mocked(api.resumeAPI.getPublicShare).mockResolvedValue(mockPublicResumeData);

    render(<PublicSharedResumePage />);

    await waitFor(() => {
      expect(screen.queryByText('Share Settings')).not.toBeInTheDocument();
      expect(screen.queryByText('Expires')).not.toBeInTheDocument();
      expect(screen.queryByText('Access Count')).not.toBeInTheDocument();
    });
  });
});
