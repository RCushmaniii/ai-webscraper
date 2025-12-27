import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { Plus, Loader2, Trash2, Eye, Globe, Settings2, RefreshCw } from 'lucide-react';
import { apiService, Crawl } from '../services/api';
import ConfirmationModal from '../components/ConfirmationModal';

const CrawlsPage: React.FC = () => {
  const [crawls, setCrawls] = useState<Crawl[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCrawls, setSelectedCrawls] = useState<Set<string>>(new Set());
  const [bulkActionLoading, setBulkActionLoading] = useState(false);

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

  const handleDelete = async (id: string) => {
    setConfirmModal({
      isOpen: true,
      title: 'Delete Crawl',
      message: 'Are you sure you want to delete this crawl? This action cannot be undone.',
      confirmText: 'Delete',
      variant: 'danger',
      onConfirm: async () => {
        setConfirmModal(prev => ({ ...prev, isOpen: false }));
        try {
          await apiService.deleteCrawl(id);
          setCrawls(crawls.filter(crawl => crawl.id !== id));
          setSelectedCrawls(prev => {
            const newSet = new Set(prev);
            newSet.delete(id);
            return newSet;
          });
          toast.success('Crawl deleted successfully');
        } catch (err) {
          console.error('Error deleting crawl:', err);
          toast.error('Failed to delete crawl');
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
        setBulkActionLoading(true);
        const deletePromises = Array.from(selectedCrawls).map(id => apiService.deleteCrawl(id));

        try {
          await Promise.all(deletePromises);
          setCrawls(crawls.filter(crawl => !selectedCrawls.has(crawl.id)));
          setSelectedCrawls(new Set());
          toast.success(`Deleted ${deletePromises.length} crawl(s) successfully`);
        } catch (err) {
          console.error('Error deleting crawls:', err);
          toast.error('Failed to delete some crawls');
        } finally {
          setBulkActionLoading(false);
        }
      },
    });
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
        const createPromises = selectedCrawlData.map(crawl =>
          apiService.createCrawl({
            url: crawl.url,
            name: `${crawl.name} (Re-run)`,
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
    const failedCrawls = crawls.filter(crawl => crawl.status === 'failed');

    if (failedCrawls.length === 0) {
      toast.info('No failed crawls to delete');
      return;
    }

    setConfirmModal({
      isOpen: true,
      title: 'Delete Failed Crawls',
      message: `Are you sure you want to delete ${failedCrawls.length} failed crawl(s)? This action cannot be undone.`,
      confirmText: `Delete ${failedCrawls.length} Failed Crawls`,
      variant: 'danger',
      onConfirm: async () => {
        setConfirmModal(prev => ({ ...prev, isOpen: false }));
        const deletePromises = failedCrawls.map(crawl => apiService.deleteCrawl(crawl.id));

        toast.promise(Promise.all(deletePromises), {
          loading: 'Deleting failed crawls...',
          success: () => {
            setCrawls(crawls.filter(crawl => crawl.status !== 'failed'));
            return `Deleted ${failedCrawls.length} failed crawl(s)`;
          },
          error: 'Failed to delete some crawls',
        });
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
              <Link
                to="/crawls/new"
                className="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium text-white bg-secondary-500 hover:bg-secondary-hover rounded-lg shadow-soft transition-colors"
              >
                <Plus className="w-5 h-5" />
                New Crawl
              </Link>
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
            <Link
              to="/crawls/new"
              className="inline-flex items-center gap-2 px-8 py-4 text-base font-medium text-white bg-secondary-500 hover:bg-secondary-hover rounded-lg shadow-soft transition-colors"
            >
              <Plus className="w-5 h-5" />
              Create First Crawl
            </Link>
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
