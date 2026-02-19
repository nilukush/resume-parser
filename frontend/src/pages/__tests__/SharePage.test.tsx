import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import SharePage from '../SharePage';
import * as api from '../../services/api';

// Mock the API module
vi.mock('../../services/api', () => ({
  resumeAPI: {
    getResume: vi.fn(),
    getShare: vi.fn(),
    createShare: vi.fn(),
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

// Mock window.open
const mockOpen = vi.fn();
window.open = mockOpen as any;

// Test data
const mockResumeData = {
  personal_info: {
    full_name: 'Test User',
    email: 'test@example.com',
    phone: '+1-555-0123',
    location: 'San Francisco, CA',
    linkedin_url: '',
    github_url: '',
    portfolio_url: '',
    summary: 'Software engineer',
  },
  work_experience: [],
  education: [],
  skills: {
    technical: ['Python', 'React'],
    soft_skills: [],
    languages: [],
    certifications: [],
    confidence: 80,
  },
  confidence_scores: {
    personal_info: 95,
    work_experience: 85,
    education: 90,
    skills: 80,
  },
};

const mockShareData = {
  share_token: 'test-token',
  share_url: 'https://resumate.app/share/test-token',
  expires_at: '2026-03-19T12:00:00Z',
  resume_id: 'test-resume-123',
  created_at: '2026-02-19T12:00:00Z',
  access_count: 5,
  is_active: true,
};

function renderWithRouter(component: React.ReactElement) {
  return render(<BrowserRouter>{component}</BrowserRouter>);
}

describe('SharePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state initially', () => {
    vi.mocked(api.resumeAPI.getShare).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    renderWithRouter(<SharePage />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('renders share link correctly', async () => {
    vi.mocked(api.resumeAPI.getShare).mockResolvedValue(mockShareData);
    vi.mocked(api.resumeAPI.getResume).mockResolvedValue({
      resume_id: 'test-resume-123',
      status: 'complete',
      data: mockResumeData,
    });

    renderWithRouter(<SharePage />);

    await waitFor(() => {
      expect(screen.getByText(/Share Your Resume/i)).toBeInTheDocument();
      expect(screen.getByText(/Share Link/i)).toBeInTheDocument();
    });
  });

  it('displays export buttons', async () => {
    vi.mocked(api.resumeAPI.getShare).mockResolvedValue(mockShareData);
    vi.mocked(api.resumeAPI.getResume).mockResolvedValue({
      resume_id: 'test-resume-123',
      status: 'complete',
      data: mockResumeData,
    });

    renderWithRouter(<SharePage />);

    await waitFor(() => {
      expect(screen.getByText(/Export As/i)).toBeInTheDocument();
      expect(screen.getByText(/PDF/i)).toBeInTheDocument();
    });
  });

  it('displays share settings', async () => {
    vi.mocked(api.resumeAPI.getShare).mockResolvedValue(mockShareData);
    vi.mocked(api.resumeAPI.getResume).mockResolvedValue({
      resume_id: 'test-resume-123',
      status: 'complete',
      data: mockResumeData,
    });

    renderWithRouter(<SharePage />);

    await waitFor(() => {
      expect(screen.getByText(/Share Settings/i)).toBeInTheDocument();
      expect(screen.getByText(/Expires in/i)).toBeInTheDocument();
    });
  });

  it('copies share link to clipboard when copy button is clicked', async () => {
    vi.mocked(api.resumeAPI.getShare).mockResolvedValue(mockShareData);
    vi.mocked(api.resumeAPI.getResume).mockResolvedValue({
      resume_id: 'test-resume-123',
      status: 'complete',
      data: mockResumeData,
    });

    // Mock navigator.clipboard.writeText
    const mockWriteText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: {
        writeText: mockWriteText,
      },
    });

    renderWithRouter(<SharePage />);

    await waitFor(() => {
      expect(screen.getByText(/Share Link/i)).toBeInTheDocument();
    });

    const copyButton = screen.getByRole('button', { name: /copy/i });
    fireEvent.click(copyButton);

    await waitFor(() => {
      expect(mockWriteText).toHaveBeenCalledWith(mockShareData.share_url);
    });
  });

  it('displays error message when share not found', async () => {
    vi.mocked(api.resumeAPI.getShare).mockRejectedValue(
      new Error('Share not found')
    );

    renderWithRouter(<SharePage />);

    await waitFor(() => {
      expect(screen.getByText(/share not found/i)).toBeInTheDocument();
    });
  });

  it('downloads PDF when PDF export button is clicked', async () => {
    vi.mocked(api.resumeAPI.getShare).mockResolvedValue(mockShareData);
    vi.mocked(api.resumeAPI.getResume).mockResolvedValue({
      resume_id: 'test-resume-123',
      status: 'complete',
      data: mockResumeData,
    });

    const mockBlob = new Blob(['pdf content'], { type: 'application/pdf' });
    vi.mocked(api.resumeAPI.exportPdf).mockResolvedValue(mockBlob);

    renderWithRouter(<SharePage />);

    await waitFor(() => {
      expect(screen.getByText(/PDF/i)).toBeInTheDocument();
    });

    const pdfButton = screen.getByRole('button', { name: /export as pdf/i });
    fireEvent.click(pdfButton);

    await waitFor(() => {
      expect(api.resumeAPI.exportPdf).toHaveBeenCalledWith('test-resume-123');
    });
  });

  it('opens WhatsApp link when WhatsApp export button is clicked', async () => {
    vi.mocked(api.resumeAPI.getShare).mockResolvedValue(mockShareData);
    vi.mocked(api.resumeAPI.getResume).mockResolvedValue({
      resume_id: 'test-resume-123',
      status: 'complete',
      data: mockResumeData,
    });

    vi.mocked(api.resumeAPI.exportWhatsapp).mockResolvedValue({
      whatsapp_url: 'https://wa.me/?text=test',
    });

    renderWithRouter(<SharePage />);

    await waitFor(() => {
      expect(screen.getByText(/WhatsApp/i)).toBeInTheDocument();
    });

    const whatsappButton = screen.getByRole('button', { name: /share on whatsapp/i });
    fireEvent.click(whatsappButton);

    await waitFor(() => {
      expect(api.resumeAPI.exportWhatsapp).toHaveBeenCalledWith('test-resume-123');
      expect(mockOpen).toHaveBeenCalledWith('https://wa.me/?text=test', '_blank');
    });
  });

  it('opens Telegram link when Telegram export button is clicked', async () => {
    vi.mocked(api.resumeAPI.getShare).mockResolvedValue(mockShareData);
    vi.mocked(api.resumeAPI.getResume).mockResolvedValue({
      resume_id: 'test-resume-123',
      status: 'complete',
      data: mockResumeData,
    });

    vi.mocked(api.resumeAPI.exportTelegram).mockResolvedValue({
      telegram_url: 'https://t.me/share/url?url=&text=test',
    });

    renderWithRouter(<SharePage />);

    await waitFor(() => {
      expect(screen.getByText(/Telegram/i)).toBeInTheDocument();
    });

    const telegramButton = screen.getByRole('button', { name: /share on telegram/i });
    fireEvent.click(telegramButton);

    await waitFor(() => {
      expect(api.resumeAPI.exportTelegram).toHaveBeenCalledWith('test-resume-123');
      expect(mockOpen).toHaveBeenCalledWith('https://t.me/share/url?url=&text=test', '_blank');
    });
  });

  it('opens email client when Email export button is clicked', async () => {
    vi.mocked(api.resumeAPI.getShare).mockResolvedValue(mockShareData);
    vi.mocked(api.resumeAPI.getResume).mockResolvedValue({
      resume_id: 'test-resume-123',
      status: 'complete',
      data: mockResumeData,
    });

    vi.mocked(api.resumeAPI.exportEmail).mockResolvedValue({
      mailto_url: 'mailto:?subject=test&body=test',
    });

    renderWithRouter(<SharePage />);

    // Get the email button using aria-label directly
    await waitFor(() => {
      expect(screen.getByLabelText('Share via Email')).toBeInTheDocument();
    });

    const emailButton = screen.getByLabelText('Share via Email');
    fireEvent.click(emailButton);

    await waitFor(() => {
      expect(api.resumeAPI.exportEmail).toHaveBeenCalledWith('test-resume-123');
      expect(mockOpen).toHaveBeenCalledWith('mailto:?subject=test&body=test', '_blank');
    });
  });

  it('revokes share when revoke button is clicked', async () => {
    vi.mocked(api.resumeAPI.getShare).mockResolvedValue(mockShareData);
    vi.mocked(api.resumeAPI.getResume).mockResolvedValue({
      resume_id: 'test-resume-123',
      status: 'complete',
      data: mockResumeData,
    });

    vi.mocked(api.resumeAPI.revokeShare).mockResolvedValue({
      message: 'Share revoked successfully',
      resume_id: 'test-resume-123',
    });

    renderWithRouter(<SharePage />);

    await waitFor(() => {
      expect(screen.getByText(/Share Settings/i)).toBeInTheDocument();
    });

    const revokeButton = screen.getByRole('button', { name: /revoke/i });
    fireEvent.click(revokeButton);

    await waitFor(() => {
      expect(api.resumeAPI.revokeShare).toHaveBeenCalledWith('test-resume-123');
    });
  });

  it('displays resume preview with personal info', async () => {
    vi.mocked(api.resumeAPI.getShare).mockResolvedValue(mockShareData);
    vi.mocked(api.resumeAPI.getResume).mockResolvedValue({
      resume_id: 'test-resume-123',
      status: 'complete',
      data: mockResumeData,
    });

    renderWithRouter(<SharePage />);

    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeInTheDocument();
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });
  });
});
