import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ReviewPage from '../ReviewPage';
import * as api from '../../services/api';

// Mock the API module
vi.mock('../../services/api', () => ({
  resumeAPI: {
    getResume: vi.fn(),
    updateResume: vi.fn(),
    createShare: vi.fn(),
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

// Test data
const mockResumeData = {
  personal_info: {
    full_name: 'John Doe',
    email: 'john@example.com',
    phone: '+1-555-0123',
    location: 'San Francisco, CA',
    linkedin_url: 'https://linkedin.com/in/johndoe',
    github_url: 'https://github.com/johndoe',
    portfolio_url: 'https://johndoe.com',
    summary: 'Software engineer with 5 years of experience',
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
      institution: 'MIT',
      degree: 'Bachelor of Science',
      field_of_study: 'Computer Science',
      location: 'Cambridge, MA',
      start_date: '2016',
      end_date: '2020',
      gpa: '3.8',
      confidence: 90,
    },
  ],
  skills: {
    technical: ['Python', 'JavaScript', 'React', 'Node.js'],
    soft_skills: ['Leadership', 'Communication'],
    languages: ['English', 'Spanish'],
    certifications: ['AWS Solutions Architect'],
    confidence: 80,
  },
  confidence_scores: {
    personal_info: 95,
    work_experience: 85,
    education: 90,
    skills: 80,
  },
};

function renderWithRouter(component: React.ReactElement) {
  return render(<BrowserRouter>{component}</BrowserRouter>);
}

describe('ReviewPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state initially', () => {
    vi.mocked(api.resumeAPI.getResume).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    renderWithRouter(<ReviewPage />);
    expect(screen.getByText(/loading resume data/i)).toBeInTheDocument();
  });

  it('displays resume data after successful load', async () => {
    vi.mocked(api.resumeAPI.getResume).mockResolvedValue({
      resume_id: 'test-resume-123',
      status: 'complete',
      data: mockResumeData,
    });

    renderWithRouter(<ReviewPage />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('john@example.com')).toBeInTheDocument();
      expect(screen.getByText('Tech Corp')).toBeInTheDocument();
      expect(screen.getByText('MIT')).toBeInTheDocument();
    });
  });

  it('displays error message when API call fails', async () => {
    vi.mocked(api.resumeAPI.getResume).mockRejectedValue(
      new Error('Resume not found')
    );

    renderWithRouter(<ReviewPage />);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });

  it('enters edit mode when Edit button is clicked', async () => {
    vi.mocked(api.resumeAPI.getResume).mockResolvedValue({
      resume_id: 'test-resume-123',
      status: 'complete',
      data: mockResumeData,
    });

    renderWithRouter(<ReviewPage />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    const editButtons = screen.getAllByText('Edit');
    expect(editButtons.length).toBeGreaterThan(0);
    fireEvent.click(editButtons[0]);

    await waitFor(() => {
      expect(screen.getByDisplayValue('John Doe')).toBeInTheDocument();
    });
  });

  it('saves changes when Save button is clicked', async () => {
    vi.mocked(api.resumeAPI.getResume).mockResolvedValue({
      resume_id: 'test-resume-123',
      status: 'complete',
      data: mockResumeData,
    });

    vi.mocked(api.resumeAPI.updateResume).mockResolvedValue({
      resume_id: 'test-resume-123',
      status: 'updated',
      data: mockResumeData,
      message: 'Resume updated successfully',
    });

    renderWithRouter(<ReviewPage />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Click Edit
    const editButtons = screen.getAllByText('Edit');
    fireEvent.click(editButtons[0]);

    await waitFor(() => {
      expect(screen.getByDisplayValue('John Doe')).toBeInTheDocument();
    });

    // Change name
    const nameInput = screen.getByDisplayValue('John Doe');
    fireEvent.change(nameInput, { target: { value: 'Jane Smith' } });

    // Click Save
    const saveButton = screen.getByText('Save');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(api.resumeAPI.updateResume).toHaveBeenCalled();
    });
  });

  it('displays work experience with confidence scores', async () => {
    vi.mocked(api.resumeAPI.getResume).mockResolvedValue({
      resume_id: 'test-resume-123',
      status: 'complete',
      data: mockResumeData,
    });

    renderWithRouter(<ReviewPage />);

    await waitFor(() => {
      expect(screen.getByText('Senior Software Engineer')).toBeInTheDocument();
    });

    // Check for confidence percentage
    const confidenceElements = screen.getAllByText('85%');
    expect(confidenceElements.length).toBeGreaterThan(0);
  });

  it('displays education with confidence scores', async () => {
    vi.mocked(api.resumeAPI.getResume).mockResolvedValue({
      resume_id: 'test-resume-123',
      status: 'complete',
      data: mockResumeData,
    });

    renderWithRouter(<ReviewPage />);

    await waitFor(() => {
      expect(screen.getByText('Bachelor of Science')).toBeInTheDocument();
    });

    // Check for confidence percentage
    const confidenceElements = screen.getAllByText('90%');
    expect(confidenceElements.length).toBeGreaterThan(0);
  });

  it('displays skills in categorized sections', async () => {
    vi.mocked(api.resumeAPI.getResume).mockResolvedValue({
      resume_id: 'test-resume-123',
      status: 'complete',
      data: mockResumeData,
    });

    renderWithRouter(<ReviewPage />);

    await waitFor(() => {
      expect(screen.getByText(/technical skills/i)).toBeInTheDocument();
      expect(screen.getByText('Python')).toBeInTheDocument();
      expect(screen.getByText('JavaScript')).toBeInTheDocument();
      expect(screen.getByText(/soft skills/i)).toBeInTheDocument();
      expect(screen.getByText('Leadership')).toBeInTheDocument();
    });
  });

  it('displays confidence scores section', async () => {
    vi.mocked(api.resumeAPI.getResume).mockResolvedValue({
      resume_id: 'test-resume-123',
      status: 'complete',
      data: mockResumeData,
    });

    renderWithRouter(<ReviewPage />);

    await waitFor(() => {
      expect(screen.getByText(/parsing confidence/i)).toBeInTheDocument();
      // Use getAllByText since 85% appears multiple times
      const confidence85 = screen.getAllByText('85%');
      const confidence90 = screen.getAllByText('90%');
      const confidence95 = screen.getAllByText('95%');
      expect(confidence85.length).toBeGreaterThan(0);
      expect(confidence90.length).toBeGreaterThan(0);
      expect(confidence95.length).toBeGreaterThan(0);
    });
  });

  it('navigates to share page when Share Resume is clicked', async () => {
    vi.mocked(api.resumeAPI.getResume).mockResolvedValue({
      resume_id: 'test-resume-123',
      status: 'complete',
      data: mockResumeData,
    });

    vi.mocked(api.resumeAPI.createShare).mockResolvedValue({
      share_token: 'test-share-token',
      share_url: 'https://example.com/share/test-share-token',
      expires_at: '2025-12-31T23:59:59Z',
    });

    renderWithRouter(<ReviewPage />);

    await waitFor(() => {
      expect(screen.getByText(/share resume/i)).toBeInTheDocument();
    });

    const shareButton = screen.getByText(/share resume/i);
    fireEvent.click(shareButton);

    await waitFor(() => {
      expect(api.resumeAPI.createShare).toHaveBeenCalledWith('test-resume-123');
    });

    expect(mockNavigate).toHaveBeenCalledWith('/share/test-resume-123');
  });
});
