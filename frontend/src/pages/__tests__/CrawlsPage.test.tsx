import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import CrawlsPage from '../CrawlsPage';
import { apiService } from '../../services/api';

// Mock the API service
jest.mock('../../services/api', () => ({
  apiService: {
    getCrawls: jest.fn(),
    getUsage: jest.fn(),
    deleteCrawl: jest.fn(),
    createCrawl: jest.fn(),
  },
}));

// Mock sonner toast
jest.mock('sonner', () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn(),
    loading: jest.fn().mockReturnValue('toast-id'),
  },
}));

const mockCrawls = [
  {
    id: 'crawl-1',
    name: 'Example Site',
    url: 'https://example.com',
    status: 'completed',
    max_depth: 3,
    max_pages: 100,
    respect_robots_txt: true,
    follow_external_links: false,
    js_rendering: false,
    rate_limit: 1,
    user_agent: '',
    created_at: '2026-01-15T10:00:00Z',
    completed_at: '2026-01-15T10:05:00Z',
    pages_crawled: 42,
  },
  {
    id: 'crawl-2',
    name: 'Test Site',
    url: 'https://test.com',
    status: 'failed',
    max_depth: 2,
    max_pages: 50,
    respect_robots_txt: true,
    follow_external_links: false,
    js_rendering: false,
    rate_limit: 1,
    user_agent: '',
    created_at: '2026-01-14T08:00:00Z',
    completed_at: null,
    pages_crawled: 0,
  },
  {
    id: 'crawl-3',
    name: 'Running Site',
    url: 'https://running.com',
    status: 'in_progress',
    max_depth: 2,
    max_pages: 50,
    respect_robots_txt: true,
    follow_external_links: false,
    js_rendering: false,
    rate_limit: 1,
    user_agent: '',
    created_at: '2026-01-16T12:00:00Z',
    completed_at: null,
    pages_crawled: 15,
  },
];

const mockUsage = {
  current_count: 3,
  limit: 10,
  is_unlimited: false,
  remaining: 7,
};

const renderCrawlsPage = () => {
  return render(
    <BrowserRouter>
      <CrawlsPage />
    </BrowserRouter>
  );
};

describe('CrawlsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (apiService.getCrawls as jest.Mock).mockResolvedValue(mockCrawls);
    (apiService.getUsage as jest.Mock).mockResolvedValue(mockUsage);
  });

  test('renders loading skeleton initially', () => {
    // Make getCrawls hang so loading state persists
    (apiService.getCrawls as jest.Mock).mockImplementation(() => new Promise(() => {}));
    renderCrawlsPage();

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  test('renders crawl list after loading', async () => {
    renderCrawlsPage();

    await waitFor(() => {
      expect(screen.getByText('Example Site')).toBeInTheDocument();
      expect(screen.getByText('Test Site')).toBeInTheDocument();
      expect(screen.getByText('Running Site')).toBeInTheDocument();
    });
  });

  test('displays crawl URLs', async () => {
    renderCrawlsPage();

    await waitFor(() => {
      expect(screen.getByText('https://example.com')).toBeInTheDocument();
      expect(screen.getByText('https://test.com')).toBeInTheDocument();
    });
  });

  test('displays status badges for each crawl', async () => {
    renderCrawlsPage();

    await waitFor(() => {
      expect(screen.getByText('completed')).toBeInTheDocument();
      expect(screen.getByText('failed')).toBeInTheDocument();
      expect(screen.getByText('in progress')).toBeInTheDocument();
    });
  });

  test('displays usage information for non-admin users', async () => {
    renderCrawlsPage();

    await waitFor(() => {
      expect(screen.getByText('7 / 10 crawls left')).toBeInTheDocument();
    });
  });

  test('shows empty state when no crawls exist', async () => {
    (apiService.getCrawls as jest.Mock).mockResolvedValue([]);
    renderCrawlsPage();

    await waitFor(() => {
      expect(screen.getByText('No crawls found')).toBeInTheDocument();
      expect(screen.getByText('Create First Crawl')).toBeInTheDocument();
    });
  });

  test('shows "New Crawl" link in header when crawls exist', async () => {
    renderCrawlsPage();

    await waitFor(() => {
      expect(screen.getByText('New Crawl')).toBeInTheDocument();
    });
  });

  test('shows "Delete Failed" button when failed crawls exist', async () => {
    renderCrawlsPage();

    await waitFor(() => {
      expect(screen.getByText('Delete 1 Failed')).toBeInTheDocument();
    });
  });

  test('does not show "Delete Failed" when no failed crawls', async () => {
    (apiService.getCrawls as jest.Mock).mockResolvedValue([mockCrawls[0]]);
    renderCrawlsPage();

    await waitFor(() => {
      expect(screen.getByText('Example Site')).toBeInTheDocument();
    });
    expect(screen.queryByText(/Delete.*Failed/)).not.toBeInTheDocument();
  });

  test('select all checkbox toggles all crawls', async () => {
    renderCrawlsPage();

    await waitFor(() => {
      expect(screen.getByText('Example Site')).toBeInTheDocument();
    });

    const selectAllCheckbox = screen.getByLabelText('Select all crawls');
    fireEvent.click(selectAllCheckbox);

    expect(screen.getByText(`All ${mockCrawls.length} crawls selected`)).toBeInTheDocument();

    // Deselect all
    fireEvent.click(selectAllCheckbox);
    expect(screen.getByText(`Select all ${mockCrawls.length} crawls`)).toBeInTheDocument();
  });

  test('individual crawl selection shows bulk action buttons', async () => {
    renderCrawlsPage();

    await waitFor(() => {
      expect(screen.getByText('Example Site')).toBeInTheDocument();
    });

    const checkbox = screen.getByLabelText('Select crawl: Example Site');
    fireEvent.click(checkbox);

    expect(screen.getByText('Re-run 1')).toBeInTheDocument();
    expect(screen.getByText('Delete 1')).toBeInTheDocument();
  });

  test('clicking delete shows confirmation modal', async () => {
    renderCrawlsPage();

    await waitFor(() => {
      expect(screen.getByText('Example Site')).toBeInTheDocument();
    });

    // Click the Delete button for the first crawl
    const deleteButtons = screen.getAllByText('Delete');
    fireEvent.click(deleteButtons[0]);

    expect(screen.getByText('Delete Crawl')).toBeInTheDocument();
    expect(screen.getByText('Are you sure you want to delete this crawl? This action cannot be undone.')).toBeInTheDocument();
  });

  test('hides unlimited usage indicator for admin users', async () => {
    (apiService.getUsage as jest.Mock).mockResolvedValue({
      current_count: 50,
      limit: null,
      is_unlimited: true,
      remaining: null,
    });
    renderCrawlsPage();

    await waitFor(() => {
      expect(screen.getByText('Example Site')).toBeInTheDocument();
    });
    expect(screen.queryByText(/crawls left/)).not.toBeInTheDocument();
  });

  test('shows upgrade button when no crawls remaining', async () => {
    (apiService.getUsage as jest.Mock).mockResolvedValue({
      current_count: 3,
      limit: 3,
      is_unlimited: false,
      remaining: 0,
    });
    renderCrawlsPage();

    await waitFor(() => {
      expect(screen.getByText('Example Site')).toBeInTheDocument();
    });
    expect(screen.getByText('Upgrade to Pro')).toBeInTheDocument();
  });
});
