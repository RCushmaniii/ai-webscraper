import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { RefreshCw } from 'lucide-react';
import { apiService, Crawl, Page, Link as CrawlLink, Issue, Image } from '../services/api';
import ConfirmationModal from '../components/ConfirmationModal';

const CrawlDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [crawl, setCrawl] = useState<Crawl | null>(null);
  const [pages, setPages] = useState<Page[]>([]);
  const [links, setLinks] = useState<CrawlLink[]>([]);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [images, setImages] = useState<Image[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('pages');
  const [pageLoading, setPageLoading] = useState(false);
  const [linkFilter, setLinkFilter] = useState<'all' | 'internal' | 'external'>('all');
  const [deleting, setDeleting] = useState(false);
  const [rerunning, setRerunning] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showRerunConfirm, setShowRerunConfirm] = useState(false);

  const fetchCrawl = async () => {
    if (!id) return;
    try {
      const crawlData = await apiService.getCrawl(id);
      setCrawl(crawlData);
    } catch (err) {
      console.error('Error fetching crawl:', err);
    }
  };

  useEffect(() => {
    if (!id) return;
    
    const fetchCrawlData = async () => {
      try {
        setLoading(true);
        
        // Fetch crawl details
        const crawlData = await apiService.getCrawl(id);
        setCrawl(crawlData);
 
        // Always fetch page inventory (v1 core dataset)
        try {
          const pagesData = await apiService.getCrawlPages(id);
          setPages(pagesData);
        } catch (err) {
          console.error('Error fetching pages:', err);
        }
        
      } catch (err) {
        console.error('Error fetching crawl:', err);
        setError('Failed to load crawl data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchCrawlData();
  }, [id]);

  const fetchTabData = async (tab: string) => {
    if (!id) return;
    
    setPageLoading(true);
    
    try {
      switch (tab) {
        case 'pages':
          if (pages.length === 0) {
            const pagesData = await apiService.getCrawlPages(id);
            setPages(pagesData);
          }
          break;
        case 'links':
          if (links.length === 0) {
            const linksData = await apiService.getCrawlLinks(id);
            setLinks(linksData);
          }
          break;
        case 'issues':
          if (issues.length === 0) {
            const issuesData = await apiService.getCrawlIssues(id);
            setIssues(issuesData);
          }
          break;
        case 'images':
          if (images.length === 0) {
            const imagesData = await apiService.getCrawlImages(id);
            setImages(imagesData);
          }
          break;
        default:
          break;
      }
    } catch (err) {
      console.error(`Error fetching ${tab}:`, err);
      setError(`Failed to load ${tab} data. Please try again later.`);
    } finally {
      setPageLoading(false);
    }
  };

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    fetchTabData(tab);
  };

  const handleDelete = async () => {
    if (!id) return;

    setDeleting(true);
    try {
      await apiService.deleteCrawl(id);
      navigate('/crawls');
    } catch (err) {
      console.error('Error deleting crawl:', err);
      setError('Failed to delete crawl. Please try again.');
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  const handleRerun = async () => {
    if (!crawl) return;

    setShowRerunConfirm(false);
    setRerunning(true);

    try {
      // Remove existing suffixes (counter, timestamp, or "(Re-run)")
      let baseName = crawl.name
        .replace(/\s*\(Re-run\)\s*/g, '')  // Remove "(Re-run)"
        .replace(/\s*#\d+\s*-\s*.+$/, '')   // Remove "#2 - Jan 15, 2:30 PM"
        .replace(/\s*#\d+$/, '')            // Remove trailing "#2"
        .trim();

      // Fetch all crawls to determine next counter
      const allCrawls = await apiService.getCrawls();

      // Find all crawls with this base name
      const pattern = new RegExp(`^${baseName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(\\s*#(\\d+))?`, 'i');
      const matchingCrawls = allCrawls.filter(c => pattern.test(c.name));

      // Determine next counter number
      const existingNumbers = matchingCrawls
        .map(c => {
          const match = c.name.match(/#(\d+)/);
          return match ? parseInt(match[1], 10) : 1;
        });

      const nextNumber = existingNumbers.length > 0 ? Math.max(...existingNumbers) + 1 : 2;

      // Create timestamp
      const timestamp = new Date().toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });

      // Create new name: "My Crawl #2 - Jan 15, 02:30 PM"
      const newName = `${baseName} #${nextNumber} - ${timestamp}`;

      await apiService.createCrawl({
        url: crawl.url,
        name: newName,
        max_depth: crawl.max_depth,
        max_pages: crawl.max_pages,
        respect_robots_txt: crawl.respect_robots_txt,
        follow_external_links: crawl.follow_external_links,
        js_rendering: crawl.js_rendering,
        rate_limit: crawl.rate_limit,
        user_agent: crawl.user_agent
      });
      toast.success('Crawl re-run initiated successfully');
      navigate('/crawls');
    } catch (err) {
      console.error('Error re-running crawl:', err);
      toast.error('Failed to re-run crawl');
    } finally {
      setRerunning(false);
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'queued':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg font-medium text-gray-500">Loading crawl data...</div>
      </div>
    );
  }

  if (error || !crawl) {
    return (
      <div className="container px-4 py-8 mx-auto">
        <div className="p-4 mb-6 text-sm text-red-700 bg-red-100 rounded-md" role="alert">
          {error || 'Crawl not found'}
        </div>
        <Link to="/crawls" className="text-secondary-500 hover:text-secondary-600">
          &larr; Back to Crawls
        </Link>
      </div>
    );
  }

  return (
    <div className="container px-4 py-8 mx-auto">
      <div className="mb-6">
        <Link to="/crawls" className="text-secondary-500 hover:text-secondary-600">
          &larr; Back to Crawls
        </Link>
      </div>

      <div className="mb-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">{crawl.name}</h1>
          <div className="flex items-center gap-3">
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusBadgeClass(crawl.status)}`}>
              {crawl.status}
            </span>
            <button
              onClick={() => setShowRerunConfirm(true)}
              disabled={rerunning}
              className="px-4 py-2 text-sm font-medium text-white bg-secondary-600 rounded-md hover:bg-secondary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-secondary-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              {rerunning ? 'Re-running...' : 'Re-run'}
            </button>
            <button
              onClick={() => setShowDeleteConfirm(true)}
              disabled={deleting}
              className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {deleting ? 'Deleting...' : 'Delete Crawl'}
            </button>
          </div>
        </div>
        <p className="mt-2 text-gray-600">
          <span className="font-medium">URL:</span> {crawl.url}
        </p>
        <div className="grid grid-cols-1 gap-4 mt-4 sm:grid-cols-2 md:grid-cols-4">
          <div className="p-3 bg-gray-50 rounded-md">
            <span className="text-sm text-gray-500">Created</span>
            <p className="text-gray-800">{formatDate(crawl.created_at)}</p>
          </div>
          <div className="p-3 bg-gray-50 rounded-md">
            <span className="text-sm text-gray-500">Max Depth</span>
            <p className="text-gray-800">{crawl.max_depth}</p>
          </div>
          <div className="p-3 bg-gray-50 rounded-md">
            <span className="text-sm text-gray-500">Max Pages</span>
            <p className="text-gray-800">{crawl.max_pages}</p>
          </div>
          <div className="p-3 bg-gray-50 rounded-md">
            <span className="text-sm text-gray-500">JavaScript Rendering</span>
            <p className="text-gray-800">{crawl.js_rendering ? 'Enabled' : 'Disabled'}</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="flex -mb-px space-x-8">
          <button
            onClick={() => handleTabChange('pages')}
            className={`py-4 text-sm font-medium border-b-2 ${
              activeTab === 'pages'
                ? 'border-secondary-500 text-secondary-500'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Pages
          </button>
          <button
            onClick={() => handleTabChange('links')}
            className={`py-4 text-sm font-medium border-b-2 ${
              activeTab === 'links'
                ? 'border-secondary-500 text-secondary-500'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Links
          </button>
          <button
            onClick={() => handleTabChange('issues')}
            className={`py-4 text-sm font-medium border-b-2 ${
              activeTab === 'issues'
                ? 'border-secondary-500 text-secondary-500'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Issues
          </button>
          <button
            onClick={() => handleTabChange('images')}
            className={`py-4 text-sm font-medium border-b-2 ${
              activeTab === 'images'
                ? 'border-secondary-500 text-secondary-500'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Images
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-lg shadow">
        {pageLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-lg font-medium text-gray-500">Loading data...</div>
          </div>
        ) : (
          <>
            {/* Pages Tab */}
            {activeTab === 'pages' && (
              <div className="p-6">
                <h2 className="mb-4 text-xl font-semibold text-gray-800">Crawled Pages</h2>
                
                {pages.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                            Title
                          </th>
                          <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                            URL
                          </th>
                          <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                            Status
                          </th>
                          <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                            Load Time (ms)
                          </th>
                          <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {pages.map((page) => (
                          <tr key={page.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4">
                              <div className="text-sm font-medium text-gray-900">{page.title || 'No title'}</div>
                            </td>
                            <td className="px-6 py-4">
                              <a 
                                href={page.url} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-sm text-secondary-600 hover:text-secondary-700 underline truncate max-w-xs block" 
                                title={page.url}
                              >
                                {page.url}
                              </a>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                page.status_code >= 200 && page.status_code < 300
                                  ? 'bg-green-100 text-green-800'
                                  : page.status_code >= 300 && page.status_code < 400
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : 'bg-red-100 text-red-800'
                              }`}>
                                {page.status_code}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-gray-500">{page.load_time_ms || 'N/A'}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <Link
                                to={`/crawls/${id}/pages/${page.id}`}
                                className="text-sm font-medium text-secondary-600 hover:text-secondary-700"
                              >
                                View Content
                              </Link>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="p-4 text-sm text-gray-700 bg-gray-100 rounded-md">
                    <p>No pages found for this crawl.</p>
                  </div>
                )}
              </div>
            )}

            {/* Links Tab */}
            {activeTab === 'links' && (
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-gray-800">Links</h2>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setLinkFilter('all')}
                      className={`px-4 py-2 text-sm font-medium rounded-md ${
                        linkFilter === 'all'
                          ? 'bg-secondary-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      All Links ({links.length})
                    </button>
                    <button
                      onClick={() => setLinkFilter('internal')}
                      className={`px-4 py-2 text-sm font-medium rounded-md ${
                        linkFilter === 'internal'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      Internal ({links.filter(l => l.is_internal).length})
                    </button>
                    <button
                      onClick={() => setLinkFilter('external')}
                      className={`px-4 py-2 text-sm font-medium rounded-md ${
                        linkFilter === 'external'
                          ? 'bg-purple-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      External ({links.filter(l => !l.is_internal).length})
                    </button>
                  </div>
                </div>

                {links.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                            Source
                          </th>
                          <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                            Target
                          </th>
                          <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                            Anchor Text
                          </th>
                          <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                            Type
                          </th>
                          <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                            Status
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {links
                          .filter(link => {
                            if (linkFilter === 'all') return true;
                            if (linkFilter === 'internal') return link.is_internal;
                            if (linkFilter === 'external') return !link.is_internal;
                            return true;
                          })
                          .map((link) => (
                          <tr key={link.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4">
                              <div className="text-sm text-gray-500 truncate max-w-xs" title={link.source_url}>
                                {link.source_url}
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <div className="text-sm text-gray-500 truncate max-w-xs" title={link.target_url}>
                                {link.target_url}
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <div className="text-sm text-gray-900 truncate max-w-xs" title={link.anchor_text}>
                                {link.anchor_text || 'No text'}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                link.is_internal
                                  ? 'bg-blue-100 text-blue-800'
                                  : 'bg-purple-100 text-purple-800'
                              }`}>
                                {link.is_internal ? 'Internal' : 'External'}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              {link.is_broken ? (
                                <span className="inline-flex px-2 py-1 text-xs font-semibold text-red-800 bg-red-100 rounded-full">
                                  Broken {link.status_code ? `(${link.status_code})` : ''}
                                </span>
                              ) : (
                                <span className="inline-flex px-2 py-1 text-xs font-semibold text-green-800 bg-green-100 rounded-full">
                                  OK {link.status_code ? `(${link.status_code})` : ''}
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="p-4 text-sm text-gray-700 bg-gray-100 rounded-md">
                    <p>No links found for this crawl.</p>
                  </div>
                )}
              </div>
            )}

            {/* Issues Tab */}
            {activeTab === 'issues' && (
              <div className="p-6">
                <h2 className="mb-4 text-xl font-semibold text-gray-800">Issues</h2>

                {issues.length > 0 ? (
                  <div className="space-y-4">
                    {issues.map((issue) => (
                      <div
                        key={issue.id}
                        className={`p-4 rounded-md ${
                          issue.severity === 'high'
                            ? 'bg-red-50 border-l-4 border-red-500'
                            : issue.severity === 'medium'
                            ? 'bg-yellow-50 border-l-4 border-yellow-500'
                            : 'bg-blue-50 border-l-4 border-blue-500'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <h3 className="text-lg font-medium text-gray-900">{issue.issue_type}</h3>
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            issue.severity === 'high'
                              ? 'bg-red-100 text-red-800'
                              : issue.severity === 'medium'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-blue-100 text-blue-800'
                          }`}>
                            {issue.severity}
                          </span>
                        </div>
                        <p className="mt-1 text-sm text-gray-600">{issue.description}</p>
                        <p className="mt-2 text-sm text-gray-500">
                          <span className="font-medium">URL:</span> {issue.url}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 text-sm text-gray-700 bg-gray-100 rounded-md">
                    <p>No issues found for this crawl.</p>
                  </div>
                )}
              </div>
            )}

            {/* Images Tab */}
            {activeTab === 'images' && (
              <div className="p-6">
                <h2 className="mb-4 text-xl font-semibold text-gray-800">Images</h2>

                {images.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                            Image
                          </th>
                          <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                            Source URL
                          </th>
                          <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                            Alt Text
                          </th>
                          <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                            Dimensions
                          </th>
                          <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                            Status
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {images.map((image) => (
                          <tr key={image.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4">
                              <img
                                src={image.src}
                                alt={image.alt || 'Image'}
                                className="w-16 h-16 object-cover rounded"
                                onError={(e) => {
                                  e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Crect fill="%23ddd" width="100" height="100"/%3E%3Ctext fill="%23999" x="50%" y="50%" text-anchor="middle" dy=".3em"%3ENo Image%3C/text%3E%3C/svg%3E';
                                }}
                              />
                            </td>
                            <td className="px-6 py-4">
                              <a
                                href={image.src}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm text-secondary-600 hover:text-secondary-700 underline truncate max-w-xs block"
                                title={image.src}
                              >
                                {image.src}
                              </a>
                            </td>
                            <td className="px-6 py-4">
                              <div className="text-sm text-gray-900 max-w-xs truncate" title={image.alt}>
                                {image.has_alt ? (
                                  <span>{image.alt || 'Empty'}</span>
                                ) : (
                                  <span className="text-red-600">Missing</span>
                                )}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-gray-500">
                                {image.width && image.height ? `${image.width} × ${image.height}` : 'N/A'}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              {image.is_broken ? (
                                <span className="inline-flex px-2 py-1 text-xs font-semibold text-red-800 bg-red-100 rounded-full">
                                  Broken {image.status_code ? `(${image.status_code})` : ''}
                                </span>
                              ) : (
                                <span className="inline-flex px-2 py-1 text-xs font-semibold text-green-800 bg-green-100 rounded-full">
                                  OK {image.status_code ? `(${image.status_code})` : ''}
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="p-4 text-sm text-gray-700 bg-gray-100 rounded-md">
                    <p>No images found for this crawl.</p>
                  </div>
                )}
              </div>
            )}

          </>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Delete Crawl</h3>
              <p className="text-gray-600 mb-4">
                Are you sure you want to delete this crawl? This will permanently remove the crawl and all associated data including:
              </p>
              <ul className="list-disc list-inside text-sm text-gray-600 mb-6 space-y-1">
                <li>All crawled pages ({pages.length} page{pages.length !== 1 ? 's' : ''})</li>
                <li>All links</li>
                <li>All SEO metadata</li>
                <li>All issues</li>
                <li>All stored files</li>
              </ul>
              <p className="text-red-600 font-medium text-sm mb-6">
                This action cannot be undone.
              </p>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  disabled={deleting}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-secondary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDelete}
                  disabled={deleting}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {deleting ? 'Deleting...' : 'Delete Permanently'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Re-run Confirmation Modal */}
      <ConfirmationModal
        isOpen={showRerunConfirm}
        onClose={() => setShowRerunConfirm(false)}
        onConfirm={handleRerun}
        title="Re-run Crawl"
        message={`Are you sure you want to re-run this crawl? This will create a new crawl job with the same settings: "${crawl.name}".`}
        confirmText="Re-run Crawl"
        variant="info"
        isLoading={rerunning}
      />
    </div>
  );
};

export default CrawlDetailPage;
