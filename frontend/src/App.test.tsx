/**
 * App.test.tsx
 *
 * TDD Tests for App routing configuration.
 *
 * Tests the routing structure for the new separated share routes:
 * - /share/:id → ShareManagementPage (owner view)
 * - /shared/:token → PublicSharedResumePage (public view)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AppRoutes } from './AppRoutes';

// Mock the pages to avoid rendering them completely
vi.mock('./pages/UploadPage', () => ({
  default: () => <div>Upload Page</div>
}));

vi.mock('./pages/ProcessingPage', () => ({
  default: () => <div>Processing Page</div>
}));

vi.mock('./pages/ReviewPage', () => ({
  default: () => <div>Review Page</div>
}));

vi.mock('./pages/ShareManagementPage', () => ({
  default: () => <div>Share Management Page</div>
}));

vi.mock('./pages/PublicSharedResumePage', () => ({
  default: () => <div>Public Shared Resume Page</div>
}));

describe('App Routing', () => {
  /**
   * TEST 1: Root route renders UploadPage
   */
  it('renders UploadPage at root path /', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AppRoutes />
      </MemoryRouter>
    );

    expect(screen.getByText('Upload Page')).toBeInTheDocument();
  });

  /**
   * TEST 2: Processing route renders ProcessingPage
   */
  it('renders ProcessingPage at /processing/:id', () => {
    render(
      <MemoryRouter initialEntries={['/processing/test-resume-id']}>
        <AppRoutes />
      </MemoryRouter>
    );

    expect(screen.getByText('Processing Page')).toBeInTheDocument();
  });

  /**
   * TEST 3: Review route renders ReviewPage
   */
  it('renders ReviewPage at /review/:id', () => {
    render(
      <MemoryRouter initialEntries={['/review/test-resume-id']}>
        <AppRoutes />
      </MemoryRouter>
    );

    expect(screen.getByText('Review Page')).toBeInTheDocument();
  });

  /**
   * TEST 4: NEW - Share management route renders ShareManagementPage
   * This is for the owner managing their share settings
   */
  it('renders ShareManagementPage at /share/:id (owner view)', () => {
    render(
      <MemoryRouter initialEntries={['/share/test-resume-id']}>
        <AppRoutes />
      </MemoryRouter>
    );

    expect(screen.getByText('Share Management Page')).toBeInTheDocument();
  });

  /**
   * TEST 5: NEW - Public shared route renders PublicSharedResumePage
   * This is for public viewers accessing shared resume
   */
  it('renders PublicSharedResumePage at /shared/:token (public view)', () => {
    render(
      <MemoryRouter initialEntries={['/shared/test-share-token']}>
        <AppRoutes />
      </MemoryRouter>
    );

    expect(screen.getByText('Public Shared Resume Page')).toBeInTheDocument();
  });
});
