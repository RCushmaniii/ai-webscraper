import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { Plus, Loader2, Trash2, Eye, Globe, Settings2, RefreshCw, Info } from 'lucide-react';
import { apiService, Crawl } from '../services/api';
import ConfirmationModal from '../components/ConfirmationModal';

interface UsageInfo {
  crawl_count: number;
  crawl_limit: number | null;
  is_admin: boolean;
  remaining_crawls: number | null;
  limit_reached: boolean;
}

const CrawlsPage: React.FC = () => {
  const [crawls, setCrawls] = useState<Crawl[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCrawls, setSelectedCrawls] = useState<Set<string>>(new Set());
  const [bulkActionLoading, setBulkActionLoading] = useState(false);
  const [usage, setUsage] = useState<UsageInfo | null>(null);

  // Confirmation modal state
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    onConfirm: () => void;
    variant?: 'danger' | 'warning' | 'info';
    confirmText?: string;
  }>({
    isOpen: false,
    title: '',
    message: '',
    onConfirm: () => {},
  });

  useEffect(() => {
    fetchCrawls();
    fetchUsage();
  }, []);

  const fetchCrawls = async () => {
    try {
      setLoading(true);
      const data = await apiService.getCrawls();
      setCrawls(data);
    } catch (err) {
      console.error('Error fetching crawls:', err);
      toast.error('Failed to load crawls. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchUsage = async () => {
    try {
      const data = await apiService.getUsage();
      setUsage(data);
    } catch (err) {
      console.error('Error fetching usage:', err);
    }
  };

  const handleDelete = async (id: string) => {
    setConfirmModal({
      isOpen: true,
      title: 'Delete Crawl',
      message: 'Are you sure you want to delete this crawl? This action cannot be undone.',
      confirmText: 'Delete',
      variant: 'danger',
      onConfirm: async () => {
        setConfirmModal(prev => ({ ...prev, isOpen: false }));

        // OPTIMISTIC UI UPDATE: Remove immediately for instant feedback
        setCrawls(prev => prev.filter(crawl => crawl.id !== id));
        setSelectedCrawls(prev => {
          const newSet = new Set(prev);
          newSet.delete(id);
          return newSet;
        });

        try {
          await apiService.deleteCrawl(id);
          toast.success('Crawl deleted');
        } catch (err: any) {
          // 404 means already deleted - that's fine
          const is404 = err?.response?.status === 404 || err?.message?.includes('404');
          if (is404) {
            toast.success('Crawl deleted');
          } else {
            console.error('Error deleting crawl:', err);
            toast.error('Failed to delete crawl');
            fetchCrawls(); // Refresh to restore accurate state
          }
        }
      },
    });
  };

  const handleSelectAll = () => {
    if (selectedCrawls.size === crawls.length) {
      setSelectedCrawls(new Set());
    } else {
      setSelectedCrawls(new Set(crawls.map(c => c.id)));
    }
  };

  const handleSelectCrawl = (id: string) => {
    setSelectedCrawls(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const handleBulkDelete = async () => {
    if (selectedCrawls.size === 0) {
      toast.info('No crawls selected');
      return;
    }

    setConfirmModal({
      isOpen: true,
      title: 'Delete Multiple Crawls',
      message: `Are you sure you want to delete ${selectedCrawls.size} selected crawl(s)? This action cannot be undone.`,
      confirmText: `Delete ${selectedCrawls.size} Crawls`,
      variant: 'danger',
      onConfirm: async () => {
        setConfirmModal(prev => ({ ...prev, isOpen: false }));
        const idsToDelete = Array.from(selectedCrawls);
        const totalCount = idsToDelete.length;

        // OPTIMISTIC UI UPDATE: Remove from list immediately for instant feedback
        setCrawls(prev => prev.filter(crawl => !selectedCrawls.has(crawl.id)));
        setSelectedCrawls(new Set());

        // Show loading toast
        const toastId = toast.loading(`Deleting ${totalCount} crawl(s)...`);

        // Use Promise.allSettled to continue even if some fail (e.g., 404 = already deleted)
        const results = await Promise.allSettled(
          idsToDelete.map(id => apiService.deleteCrawl(id))
        );

        // Count successes and failures
        // Note: 404 means "not found" = already deleted = success from user's perspective
        const succeeded = results.filter(r => r.status === 'fulfilled').length;
        const alreadyDeleted = results.filter(r =>
          r.status === 'rejected' &&
          (r.reason?.response?.status === 404 || r.reason?.message?.includes('404'))
        ).length;
        const failed = results.filter(r =>
          r.status === 'rejected' &&
          !(r.reason?.response?.status === 404 || r.reason?.message?.includes('404'))
        ).length;

        // Update toast with result
        if (failed === 0) {
          toast.success(`Deleted ${totalCount} crawl(s)`, { id: toastId });
        } else {
          toast.error(`Deleted ${succeeded + alreadyDeleted} of ${totalCount}. ${failed} failed.`, { id: toastId });
          // Refresh list to get accurate state from server
          fetchCrawls();
        }
      },
    });
  };

  // Helper: Generate incremented rerun name (same logic as CrawlDetailPage)
  const generateRerunName = (crawlName: string, allCrawls: Crawl[], reservedNumbers: Map<string, number>): string => {
    // Remove existing suffixes (counter, timestamp, or "(Re-run)")
    let baseName = crawlName
      .replace(/\s*\(Re-run\)\s*/g, '')  // Remove "(Re-run)"
      .replace(/\s*#\d+\s*-\s*.+$/, '')   // Remove "#2 - Jan 15, 2:30 PM"
      .replace(/\s*#\d+$/, '')            // Remove trailing "#2"
      .trim();

    // Find all crawls with this base name
    const pattern = new RegExp(`^${baseName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(\\s*#(\\d+))?`, 'i');
    const matchingCrawls = allCrawls.filter(c => pattern.test(c.name));

    // Determine next counter number from existing crawls
    const existingNumbers = matchingCrawls
      .map(c => {
        const match = c.name.match(/#(\d+)/);
        return match ? parseInt(match[1], 10) : 1;
      });

    // Also consider numbers we've already reserved in this batch
    const reserved = reservedNumbers.get(baseName) || 0;
    const maxExisting = existingNumbers.length > 0 ? Math.max(...existingNumbers) : 1;
    const nextNumber = Math.max(maxExisting, reserved) + 1;

    // Reserve this number for the base name
    reservedNumbers.set(baseName, nextNumber);

    // Create timestamp (Mexico City timezone)
    const timestamp = new Date().toLocaleString('en-US', {
      timeZone: 'America/Mexico_City',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });

    // Create new name: "My Crawl #2 - Jan 15, 02:30 PM"
    return `${baseName} #${nextNumber} - ${timestamp}`;
  };

  const handleBulkRerun = async () => {
    if (selectedCrawls.size === 0) {
      toast.info('No crawls selected');
      return;
    }

    setConfirmModal({
      isOpen: true,
      title: 'Re-run Multiple Crawls',
      message: `Are you sure you want to re-run ${selectedCrawls.size} selected crawl(s)? This will create new crawl jobs with the same settings.`,
      confirmText: `Re-run ${selectedCrawls.size} Crawls`,
      variant: 'info',
      onConfirm: async () => {
        setConfirmModal(prev => ({ ...prev, isOpen: false }));
        setBulkActionLoading(true);
        const selectedCrawlData = crawls.filter(c => selectedCrawls.has(c.id));

        // Track reserved numbers to handle multiple crawls with same base name
        const reservedNumbers = new Map<string, number>();

        const createPromises = selectedCrawlData.map(crawl =>
          apiService.createCrawl({
            url: crawl.url,
            name: generateRerunName(crawl.name, crawls, reservedNumbers),
            max_depth: crawl.max_depth,
            max_pages: crawl.max_pages,
            respect_robots_txt: crawl.respect_robots_txt,
            follow_external_links: crawl.follow_external_links,
            js_rendering: crawl.js_rendering,
            rate_limit: crawl.rate_limit,
            user_agent: crawl.user_agent
          })
        );

        try {
          await Promise.all(createPromises);
          setSelectedCrawls(new Set());
          toast.success(`Re-running ${createPromises.length} crawl(s)`);
          fetchCrawls();
        } catch (err) {
          console.error('Error re-running crawls:', err);
          toast.error('Failed to re-run some crawls');
        } finally {
          setBulkActionLoading(false);
        }
      },
    });
  };

  const handleDeleteFailedCrawls = async () => {
    const failedCrawlsList = crawls.filter(crawl => crawl.status === 'failed');

    if (failedCrawlsList.length === 0) {
      toast.info('No failed crawls to delete');
      return;
    }

    setConfirmModal({
      isOpen: true,
      title: 'Delete Failed Crawls',
      message: `Are you sure you want to delete ${failedCrawlsList.length} failed crawl(s)? This action cannot be undone.`,
      confirmText: `Delete ${failedCrawlsList.length} Failed Crawls`,
      variant: 'danger',
      onConfirm: async () => {
        setConfirmModal(prev => ({ ...prev, isOpen: false }));
        const idsToDelete = failedCrawlsList.map(c => c.id);
        const totalCount = idsToDelete.length;

        // OPTIMISTIC UI UPDATE: Remove failed crawls immediately
        setCrawls(prev => prev.filter(crawl => crawl.status !== 'failed'));

        // Show loading toast
        const toastId = toast.loading(`Deleting ${totalCount} failed crawl(s)...`);

        // Use Promise.allSettled to continue even if some fail
        const results = await Promise.allSettled(
          idsToDelete.map(id => apiService.deleteCrawl(id))
        );

        // Count results (404 = already deleted = success)
        const failed = results.filter(r =>
          r.status === 'rejected' &&
          !(r.reason?.response?.status === 404 || r.reason?.message?.includes('404'))
        ).length;

        if (failed === 0) {
          toast.success(`Deleted ${totalCount} failed crawl(s)`, { id: toastId });
        } else {
          toast.error(`Deleted ${totalCount - failed} of ${totalCount}. ${failed} failed.`, { id: toastId });
          fetchCrawls(); // Refresh to get accurate state
        }
      },
    });
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      completed: 'bg-success-100 text-success-600 border-success-200',
      in_progress: 'bg-secondary-100 text-secondary-600 border-secondary-200',
      queued: 'bg-yellow-100 text-yellow-700 border-yellow-200',
      failed: 'bg-error-100 text-error-600 border-error-200',
    };

    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-lg text-xs font-medium border ${styles[status as keyof typeof styles] || 'bg-primary-100 text-primary-600 border-primary-200'}`}>
        {status.replace('_', ' ')}
      </span>
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      timeZone: 'America/Mexico_City',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const failedCount = crawls.filter(crawl => crawl.status === 'failed').length;
  const hasCrawls = crawls.length > 0;

  return (
    <div className="max-w-7xl mx-auto" style={{ padding: '4rem 2rem' }}>
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-neutral-charcoal">Crawls</h1>
            <p className="mt-2 text-base text-neutral-steel leading-comfortable">
              Manage and monitor your website crawl operations
            </p>
          </div>
          {hasCrawls && (
            <div className="flex items-center gap-3">
              {selectedCrawls.size > 0 && (
                <>
                  <button
                    onClick={handleBulkRerun}
                    disabled={bulkActionLoading}
                    className="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium text-secondary-600 bg-secondary-50 hover:bg-secondary-100 border border-secondary-200 rounded-lg shadow-soft transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Re-run {selectedCrawls.size}
                  </button>
                  <button
                    onClick={handleBulkDelete}
                    disabled={bulkActionLoading}
                    className="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium text-error-600 bg-error-50 hover:bg-error-100 border border-error-200 rounded-lg shadow-soft transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete {selectedCrawls.size}
                  </button>
                </>
              )}
              {failedCount > 0 && selectedCrawls.size === 0 && (
                <button
                  onClick={handleDeleteFailedCrawls}
                  className="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium text-error-600 bg-error-50 hover:bg-error-100 border border-error-200 rounded-lg shadow-soft transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete {failedCount} Failed
                </button>
              )}
              {/* Usage indicator for non-admin users */}
              {usage && !usage.is_admin && (
                <div className="flex items-center gap-2 px-4 py-2 bg-secondary-50 border border-secondary-200 rounded-lg">
                  <Info className="w-4 h-4 text-secondary-600" />
                  <span className="text-sm text-secondary-700 font-medium">
                    {usage.remaining_crawls} / {usage.crawl_limit} crawls left
                  </span>
                </div>
              )}
              {usage?.limit_reached ? (
                <button
                  onClick={() => toast.info('Pro upgrade coming soon!')}
                  className="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium text-white bg-secondary-500 hover:bg-secondary-hover rounded-lg shadow-soft transition-colors"
                >
                  <Plus className="w-5 h-5" />
                  Upgrade to Pro
                </button>
              ) : (
                <Link
                  to="/crawls/new"
                  className="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium text-white bg-secondary-500 hover:bg-secondary-hover rounded-lg shadow-soft transition-colors"
                >
                  <Plus className="w-5 h-5" />
                  New Crawl
                </Link>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Loading State */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-24">
          <Loader2 className="w-10 h-10 text-secondary-500 animate-spin mb-4" />
          <p className="text-sm text-neutral-steel">Loading crawls...</p>
        </div>
      ) : hasCrawls ? (
        /* Crawls List - Plush cards */
        <div className="space-y-4">
          {/* Select All Bar */}
          {crawls.length > 0 && (
            <div className="bg-primary-50 rounded-lg border border-primary-200 px-6 py-3 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={selectedCrawls.size === crawls.length && crawls.length > 0}
                  onChange={handleSelectAll}
                  className="w-4 h-4 text-secondary-500 border-primary-300 rounded focus:ring-secondary-500 cursor-pointer"
                />
                <span className="text-sm font-medium text-neutral-charcoal">
                  {selectedCrawls.size === crawls.length && crawls.length > 0
                    ? `All ${crawls.length} crawls selected`
                    : selectedCrawls.size > 0
                    ? `${selectedCrawls.size} of ${crawls.length} selected`
                    : `Select all ${crawls.length} crawls`}
                </span>
              </div>
              {selectedCrawls.size > 0 && (
                <button
                  onClick={() => setSelectedCrawls(new Set())}
                  className="text-sm text-secondary-600 hover:text-secondary-700 font-medium"
                >
                  Clear selection
                </button>
              )}
            </div>
          )}

          {crawls.map((crawl) => (
            <div
              key={crawl.id}
              className="bg-white rounded-lg border border-primary-100 hover:border-secondary-200 hover:shadow-soft transition-all overflow-hidden"
            >
              <div style={{ padding: '2rem' }}>
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <input
                      type="checkbox"
                      checked={selectedCrawls.has(crawl.id)}
                      onChange={() => handleSelectCrawl(crawl.id)}
                      className="mt-1 w-4 h-4 text-secondary-500 border-primary-300 rounded focus:ring-secondary-500 cursor-pointer"
                      onClick={(e) => e.stopPropagation()}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-3">
                        <Link
                          to={`/crawls/${crawl.id}`}
                          className="text-xl font-semibold text-neutral-charcoal hover:text-secondary-500 transition-colors"
                        >
                          {crawl.name}
                        </Link>
                        {getStatusBadge(crawl.status)}
                      </div>
                      <div className="space-y-2">
                        <p className="flex items-center gap-2 text-sm text-neutral-steel">
                          <Globe className="w-4 h-4" />
                          {crawl.url.length > 60 ? `${crawl.url.substring(0, 60)}...` : crawl.url}
                        </p>
                        <p className="flex items-center gap-2 text-sm text-neutral-steel">
                          <Settings2 className="w-4 h-4" />
                          Depth: {crawl.max_depth} • Max Pages: {crawl.max_pages}
                        </p>
                        <p className="text-xs text-neutral-steel/70 mt-3">
                          Created {formatDate(crawl.created_at)}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 ml-6">
                    <Link
                      to={`/crawls/${crawl.id}`}
                      className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-secondary-600 bg-secondary-50 hover:bg-secondary-100 rounded-lg transition-colors"
                    >
                      <Eye className="w-4 h-4" />
                      View
                    </Link>
                    <button
                      onClick={() => handleDelete(crawl.id)}
                      className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-error-600 bg-error-50 hover:bg-error-100 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Empty State - Plush centered hero panel */
        <div className="bg-white rounded-lg shadow-soft-lg border border-primary-100" style={{ padding: '4rem 3rem' }}>
          <div className="text-center max-w-lg mx-auto">
            <div className="w-20 h-20 bg-primary-50 rounded-full flex items-center justify-center mx-auto mb-6">
              <Globe className="w-10 h-10 text-primary-300" />
            </div>
            <h3 className="text-2xl font-semibold text-neutral-charcoal mb-3">
              No crawls found
            </h3>
            <p className="text-base text-neutral-steel mb-8 leading-comfortable">
              Start your first site analysis to begin crawling and inspecting web pages
            </p>
            {usage?.limit_reached ? (
              <button
                onClick={() => toast.info('Pro upgrade coming soon!')}
                className="inline-flex items-center gap-2 px-8 py-4 text-base font-medium text-white bg-secondary-500 hover:bg-secondary-hover rounded-lg shadow-soft transition-colors"
              >
                <Plus className="w-5 h-5" />
                Upgrade to Pro
              </button>
            ) : (
              <Link
                to="/crawls/new"
                className="inline-flex items-center gap-2 px-8 py-4 text-base font-medium text-white bg-secondary-500 hover:bg-secondary-hover rounded-lg shadow-soft transition-colors"
              >
                <Plus className="w-5 h-5" />
                Create First Crawl
              </Link>
            )}
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      <ConfirmationModal
        isOpen={confirmModal.isOpen}
        onClose={() => setConfirmModal(prev => ({ ...prev, isOpen: false }))}
        onConfirm={confirmModal.onConfirm}
        title={confirmModal.title}
        message={confirmModal.message}
        confirmText={confirmModal.confirmText}
        variant={confirmModal.variant}
      />
    </div>
  );
};

export default CrawlsPage;
