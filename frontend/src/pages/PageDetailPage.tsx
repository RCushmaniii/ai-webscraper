import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  ExternalLink,
  Copy,
  Check,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Gauge,
  ChevronDown,
  ChevronRight,
  FileText,
  Link2,
  Image as ImageIcon,
  Code,
  Clock,
  HardDrive,
  AlertCircle,
  Download,
  FileCode,
  FileJson,
  Type,
  ChevronLeft
} from 'lucide-react';
import { toast } from 'sonner';
import { apiService, Link as CrawlLink, Image } from '../services/api';

interface PageData {
  id: string;
  crawl_id: string;
  url: string;
  title: string;
  meta_description: string | null;
  content_summary: string;
  full_content?: string;
  status_code: number;
  response_time: number;
  load_time_ms?: number;
  render_ms?: number;
  content_type: string;
  content_length: number;
  page_size_bytes?: number;
  h1_tags: string[];
  h2_tags: string[];
  h3_tags?: string[];
  internal_links: number;
  external_links: number;
  images: number;
  word_count?: number;
  canonical_url?: string;
  created_at: string;
}

const PageDetailPage: React.FC = () => {
  const { crawlId, pageId } = useParams<{ crawlId: string; pageId: string }>();
  const [page, setPage] = useState<PageData | null>(null);
  const [links, setLinks] = useState<CrawlLink[]>([]);
  const [images, setImages] = useState<Image[]>([]);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'links' | 'images'>('overview');
  const [technicalExpanded, setTechnicalExpanded] = useState(false);
  const [contentTab, setContentTab] = useState<'reader' | 'raw'>('reader');
  const [contentExpanded, setContentExpanded] = useState(false);
  const [exportMenuOpen, setExportMenuOpen] = useState(false);
  const exportMenuRef = useRef<HTMLDivElement>(null);
  const thumbnailScrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchPageData();
  }, [pageId]);

  const fetchPageData = async () => {
    if (!crawlId || !pageId) return;

    try {
      setLoading(true);
      const data = await apiService.getPageDetail(crawlId, pageId);
      setPage(data);

      // Fetch links and images for this page
      const [linksData, imagesData] = await Promise.all([
        apiService.getPageLinks(crawlId, pageId).catch(() => []),
        apiService.getPageImages(crawlId, pageId).catch(() => [])
      ]);
      setLinks(linksData);
      setImages(imagesData);
    } catch (err) {
      console.error('Error fetching page:', err);
      toast.error('Failed to load page data');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyContent = (format: 'text' | 'markdown' | 'html' | 'json' = 'text') => {
    const content = page?.full_content || page?.content_summary;
    if (!content || !page) return;

    let exportContent = '';
    let successMessage = '';

    switch (format) {
      case 'markdown':
        exportContent = `# ${page.title || 'Untitled'}\n\n**URL:** ${page.url}\n\n---\n\n${content}`;
        successMessage = 'Markdown copied to clipboard';
        break;
      case 'html':
        exportContent = `<!DOCTYPE html>
<html>
<head>
  <title>${page.title || 'Untitled'}</title>
  <meta name="description" content="${page.meta_description || ''}">
</head>
<body>
  <h1>${page.title || 'Untitled'}</h1>
  <p>${content}</p>
</body>
</html>`;
        successMessage = 'HTML copied to clipboard';
        break;
      case 'json':
        exportContent = JSON.stringify({
          url: page.url,
          title: page.title,
          meta_description: page.meta_description,
          content: content,
          word_count: wordCount,
          status_code: page.status_code,
          crawled_at: page.created_at
        }, null, 2);
        successMessage = 'JSON copied to clipboard';
        break;
      default:
        exportContent = content;
        successMessage = 'Content copied to clipboard';
    }

    navigator.clipboard.writeText(exportContent);
    setCopied(true);
    setExportMenuOpen(false);
    toast.success(successMessage);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadJSON = () => {
    if (!page) return;
    const content = page.full_content || page.content_summary;
    const data = {
      url: page.url,
      title: page.title,
      meta_description: page.meta_description,
      content: content,
      h1_tags: page.h1_tags,
      h2_tags: page.h2_tags,
      status_code: page.status_code,
      response_time: page.response_time,
      crawled_at: page.created_at
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `page-${pageId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setExportMenuOpen(false);
    toast.success('JSON file downloaded');
  };

  // Close export menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (exportMenuRef.current && !exportMenuRef.current.contains(event.target as Node)) {
        setExportMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Thumbnail scroll handlers
  const scrollThumbnails = (direction: 'left' | 'right') => {
    if (thumbnailScrollRef.current) {
      const scrollAmount = 200;
      thumbnailScrollRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      });
    }
  };

  // Format content for reader view (basic markdown-like rendering)
  const formatReaderContent = (text: string) => {
    if (!text) return '';
    // Basic formatting - convert line breaks, preserve paragraphs
    return text
      .split(/\n\n+/)
      .map(p => p.trim())
      .filter(p => p.length > 0)
      .join('\n\n');
  };

  // Performance helpers
  const getResponseTimeStatus = (ms: number) => {
    if (ms < 500) return { color: 'green', label: 'Fast', percentage: 20 };
    if (ms < 1000) return { color: 'lime', label: 'Good', percentage: 40 };
    if (ms < 2000) return { color: 'yellow', label: 'Moderate', percentage: 60 };
    if (ms < 4000) return { color: 'orange', label: 'Slow', percentage: 80 };
    return { color: 'red', label: 'Very Slow', percentage: 100 };
  };

  const getStatusCodeInfo = (code: number) => {
    if (code >= 200 && code < 300) return { color: 'green', label: 'Success' };
    if (code >= 300 && code < 400) return { color: 'yellow', label: 'Redirect' };
    if (code >= 400 && code < 500) return { color: 'red', label: 'Client Error' };
    if (code >= 500) return { color: 'red', label: 'Server Error' };
    return { color: 'gray', label: 'Unknown' };
  };

  const getMetaDescriptionStatus = (desc: string | null) => {
    if (!desc) return { status: 'missing', icon: XCircle, color: 'red', message: 'Missing' };
    const len = desc.length;
    if (len < 50) return { status: 'short', icon: AlertTriangle, color: 'yellow', message: `Too short (${len}/160)` };
    if (len > 160) return { status: 'long', icon: AlertTriangle, color: 'yellow', message: `Too long (${len}/160)` };
    return { status: 'good', icon: CheckCircle2, color: 'green', message: `Good (${len}/160)` };
  };

  // Calculate word count from content
  const calculateWordCount = (content: string | null | undefined): number => {
    if (!content) return 0;
    return content.trim().split(/\s+/).filter(word => word.length > 0).length;
  };

  // Calculate other links (anchors, mailto, tel, etc.)
  const calculateLinkBreakdown = () => {
    const internal = links.filter(l => l.is_internal).length;
    const external = links.filter(l => !l.is_internal).length;
    const total = links.length;
    // "Other" links would be anchors (#), mailto:, tel:, javascript:, etc.
    // Since we're working with what we have, calculate from page data if available
    const pageInternal = page?.internal_links || internal;
    const pageExternal = page?.external_links || external;
    const pageTotal = pageInternal + pageExternal;
    const other = Math.max(0, total - internal - external);

    return { internal, external, other, total };
  };

  // Count images missing alt text
  const getImageAltStats = () => {
    const total = images.length;
    const withAlt = images.filter(img => img.has_alt).length;
    const missingAlt = total - withAlt;
    return { total, withAlt, missingAlt };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg font-medium text-gray-500">Loading page data...</div>
      </div>
    );
  }

  if (!page) {
    return (
      <div className="container px-4 py-8 mx-auto">
        <div className="p-4 mb-6 text-sm text-red-700 bg-red-100 rounded-md">
          Page not found
        </div>
        <Link to={`/crawls/${crawlId}`} className="text-secondary-500 hover:text-secondary-600">
          &larr; Back to Crawl
        </Link>
      </div>
    );
  }

  const responseTime = page.load_time_ms || page.render_ms || page.response_time || 0;
  const responseStatus = getResponseTimeStatus(responseTime);
  const statusInfo = getStatusCodeInfo(page.status_code);
  const metaStatus = getMetaDescriptionStatus(page.meta_description);
  const linkBreakdown = calculateLinkBreakdown();
  const imageStats = getImageAltStats();
  const wordCount = page.word_count || calculateWordCount(page.full_content || page.content_summary);
  const pageSize = page.page_size_bytes || page.content_length || 0;

  return (
    <div className="container px-4 py-8 mx-auto max-w-4xl">
      {/* Back Link */}
      <div className="mb-6">
        <Link to={`/crawls/${crawlId}`} className="inline-flex items-center gap-2 text-secondary-500 hover:text-secondary-600">
          <ArrowLeft className="w-4 h-4" />
          Back to Crawl
        </Link>
      </div>

      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2 leading-tight">
          {page.title || 'Untitled Page'}
        </h1>
        <a
          href={page.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-sm text-secondary-500 hover:text-secondary-600 break-all"
        >
          {page.url}
          <ExternalLink className="w-3.5 h-3.5 flex-shrink-0" />
        </a>
      </div>

      {/* Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="flex -mb-px space-x-8">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-4 text-sm font-medium border-b-2 ${
              activeTab === 'overview'
                ? 'border-secondary-500 text-secondary-500'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('links')}
            className={`py-4 text-sm font-medium border-b-2 ${
              activeTab === 'links'
                ? 'border-secondary-500 text-secondary-500'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Links ({links.length})
          </button>
          <button
            onClick={() => setActiveTab('images')}
            className={`py-4 text-sm font-medium border-b-2 ${
              activeTab === 'images'
                ? 'border-secondary-500 text-secondary-500'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Images ({images.length})
          </button>
        </nav>
      </div>

      {/* Overview Tab - Vertical Card Layout */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Card 1: Health & Performance */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
              <div className="flex items-center gap-2">
                <Gauge className="w-5 h-5 text-gray-600" />
                <h2 className="text-lg font-semibold text-gray-900">Health & Performance</h2>
              </div>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                {/* Status Code */}
                <div>
                  <div className="text-sm text-gray-500 mb-1">Status Code</div>
                  <div className="flex items-center gap-2">
                    <span className={`inline-flex px-2.5 py-1 text-sm font-semibold rounded-full ${
                      statusInfo.color === 'green' ? 'bg-green-100 text-green-800' :
                      statusInfo.color === 'yellow' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {page.status_code}
                    </span>
                    <span className="text-xs text-gray-500">{statusInfo.label}</span>
                  </div>
                </div>

                {/* Response Time with Visual Indicator */}
                <div>
                  <div className="text-sm text-gray-500 mb-1">Response Time</div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xl font-semibold ${
                      responseStatus.color === 'green' ? 'text-green-600' :
                      responseStatus.color === 'lime' ? 'text-lime-600' :
                      responseStatus.color === 'yellow' ? 'text-yellow-600' :
                      responseStatus.color === 'orange' ? 'text-orange-600' :
                      'text-red-600'
                    }`}>
                      {responseTime}ms
                    </span>
                  </div>
                  {/* Performance Bar */}
                  <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        responseStatus.color === 'green' ? 'bg-green-500' :
                        responseStatus.color === 'lime' ? 'bg-lime-500' :
                        responseStatus.color === 'yellow' ? 'bg-yellow-500' :
                        responseStatus.color === 'orange' ? 'bg-orange-500' :
                        'bg-red-500'
                      }`}
                      style={{ width: `${responseStatus.percentage}%` }}
                    />
                  </div>
                  <div className="text-xs text-gray-500 mt-1">{responseStatus.label}</div>
                </div>

                {/* Page Size */}
                <div>
                  <div className="text-sm text-gray-500 mb-1">Page Size</div>
                  <div className="flex items-center gap-2">
                    <HardDrive className="w-4 h-4 text-gray-400" />
                    <span className="text-xl font-semibold text-gray-900">
                      {(pageSize / 1024).toFixed(1)}KB
                    </span>
                  </div>
                </div>

                {/* Crawled At */}
                <div>
                  <div className="text-sm text-gray-500 mb-1">Crawled At</div>
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-900">
                      {new Date(page.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Card 2: SEO & Meta */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-gray-600" />
                <h2 className="text-lg font-semibold text-gray-900">SEO & Meta</h2>
              </div>
            </div>
            <div className="p-6 space-y-4">
              {/* Page Title */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-gray-700">Page Title</span>
                  {page.title ? (
                    <span className="text-xs text-gray-500">{page.title.length} characters</span>
                  ) : (
                    <span className="text-xs text-red-500 flex items-center gap-1">
                      <XCircle className="w-3 h-3" /> Missing
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md">
                  {page.title || <span className="text-red-500 italic">No title found</span>}
                </p>
              </div>

              {/* Meta Description */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-gray-700">Meta Description</span>
                  <span className={`text-xs flex items-center gap-1 ${
                    metaStatus.color === 'green' ? 'text-green-600' :
                    metaStatus.color === 'yellow' ? 'text-yellow-600' :
                    'text-red-600'
                  }`}>
                    <metaStatus.icon className="w-3 h-3" />
                    {metaStatus.message}
                  </span>
                </div>
                <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md">
                  {page.meta_description || <span className="text-red-500 italic">No meta description found</span>}
                </p>
                {/* Character Progress Bar */}
                {page.meta_description && (
                  <div className="mt-2">
                    <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          page.meta_description.length <= 160 ? 'bg-green-500' : 'bg-yellow-500'
                        }`}
                        style={{ width: `${Math.min((page.meta_description.length / 160) * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Canonical URL */}
              {page.canonical_url && (
                <div>
                  <span className="text-sm font-medium text-gray-700">Canonical URL</span>
                  <p className="text-sm text-secondary-600 bg-gray-50 p-3 rounded-md mt-1 break-all">
                    {page.canonical_url}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Card 3: Link Analysis */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
              <div className="flex items-center gap-2">
                <Link2 className="w-5 h-5 text-gray-600" />
                <h2 className="text-lg font-semibold text-gray-900">Link Analysis</h2>
              </div>
            </div>
            <div className="p-6">
              {/* Total Count */}
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm text-gray-600">Total Links</span>
                <span className="text-2xl font-bold text-gray-900">{linkBreakdown.total}</span>
              </div>

              {/* Segmented Progress Bar (GitHub-style) */}
              {linkBreakdown.total > 0 && (
                <div className="mb-4">
                  <div className="h-3 bg-gray-200 rounded-full overflow-hidden flex">
                    {linkBreakdown.internal > 0 && (
                      <div
                        className="bg-blue-500 h-full"
                        style={{ width: `${(linkBreakdown.internal / linkBreakdown.total) * 100}%` }}
                        title={`Internal: ${linkBreakdown.internal}`}
                      />
                    )}
                    {linkBreakdown.external > 0 && (
                      <div
                        className="bg-purple-500 h-full"
                        style={{ width: `${(linkBreakdown.external / linkBreakdown.total) * 100}%` }}
                        title={`External: ${linkBreakdown.external}`}
                      />
                    )}
                    {linkBreakdown.other > 0 && (
                      <div
                        className="bg-gray-400 h-full"
                        style={{ width: `${(linkBreakdown.other / linkBreakdown.total) * 100}%` }}
                        title={`Other: ${linkBreakdown.other}`}
                      />
                    )}
                  </div>
                </div>
              )}

              {/* Breakdown Legend */}
              <div className="grid grid-cols-3 gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                  <div>
                    <div className="text-sm font-medium text-gray-900">{linkBreakdown.internal}</div>
                    <div className="text-xs text-gray-500">Internal</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-purple-500"></div>
                  <div>
                    <div className="text-sm font-medium text-gray-900">{linkBreakdown.external}</div>
                    <div className="text-xs text-gray-500">External</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-gray-400"></div>
                  <div>
                    <div className="text-sm font-medium text-gray-900">{linkBreakdown.other}</div>
                    <div className="text-xs text-gray-500">Other</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Card 4: Page Structure (Headings) */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
              <div className="flex items-center gap-2">
                <Code className="w-5 h-5 text-gray-600" />
                <h2 className="text-lg font-semibold text-gray-900">Page Structure</h2>
              </div>
            </div>
            <div className="p-6">
              {/* H1 Warning Banner */}
              {page.h1_tags.length === 0 && (
                <div className="flex items-center gap-2 p-3 mb-4 bg-red-50 border border-red-200 rounded-md">
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
                  <span className="text-sm text-red-700">Missing H1 tag - This is important for SEO!</span>
                </div>
              )}
              {page.h1_tags.length > 1 && (
                <div className="flex items-center gap-2 p-3 mb-4 bg-yellow-50 border border-yellow-200 rounded-md">
                  <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0" />
                  <span className="text-sm text-yellow-700">Multiple H1 tags found ({page.h1_tags.length}) - Best practice is to have only one H1 per page</span>
                </div>
              )}

              {/* Heading Tree View */}
              <div className="space-y-2">
                {page.h1_tags.length > 0 ? (
                  page.h1_tags.map((h1, idx) => (
                    <div key={`h1-${idx}`} className="space-y-1">
                      <div className="flex items-start gap-2 p-2 bg-blue-50 rounded-md">
                        <span className="px-1.5 py-0.5 text-xs font-bold text-blue-700 bg-blue-200 rounded">H1</span>
                        <span className="text-sm text-gray-900">{h1}</span>
                      </div>
                      {/* H2 tags indented under H1 */}
                      {page.h2_tags.length > 0 && idx === 0 && (
                        <div className="ml-6 space-y-1">
                          {page.h2_tags.map((h2, h2idx) => (
                            <div key={`h2-${h2idx}`} className="flex items-start gap-2 p-2 bg-gray-50 rounded-md">
                              <span className="px-1.5 py-0.5 text-xs font-bold text-gray-600 bg-gray-200 rounded">H2</span>
                              <span className="text-sm text-gray-700">{h2}</span>
                            </div>
                          ))}
                          {/* H3 tags if available */}
                          {page.h3_tags && page.h3_tags.length > 0 && (
                            <div className="ml-6 space-y-1">
                              {page.h3_tags.slice(0, 5).map((h3, h3idx) => (
                                <div key={`h3-${h3idx}`} className="flex items-start gap-2 p-2 bg-gray-50/50 rounded-md">
                                  <span className="px-1.5 py-0.5 text-xs font-bold text-gray-500 bg-gray-100 rounded">H3</span>
                                  <span className="text-sm text-gray-600">{h3}</span>
                                </div>
                              ))}
                              {page.h3_tags.length > 5 && (
                                <div className="text-xs text-gray-500 ml-8">
                                  +{page.h3_tags.length - 5} more H3 tags...
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-gray-500 italic">No heading tags found</div>
                )}

                {/* Show H2s without H1 parent */}
                {page.h1_tags.length === 0 && page.h2_tags.length > 0 && (
                  <div className="space-y-1">
                    {page.h2_tags.map((h2, idx) => (
                      <div key={`h2-${idx}`} className="flex items-start gap-2 p-2 bg-gray-50 rounded-md">
                        <span className="px-1.5 py-0.5 text-xs font-bold text-gray-600 bg-gray-200 rounded">H2</span>
                        <span className="text-sm text-gray-700">{h2}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Card 5: Content & Assets (Enhanced) */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ImageIcon className="w-5 h-5 text-gray-600" />
                  <h2 className="text-lg font-semibold text-gray-900">Content & Assets</h2>
                </div>
                {/* Export Dropdown */}
                <div className="relative" ref={exportMenuRef}>
                  <button
                    onClick={() => setExportMenuOpen(!exportMenuOpen)}
                    className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 rounded-md transition-colors"
                  >
                    {copied ? (
                      <>
                        <Check className="w-4 h-4 text-green-600" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Download className="w-4 h-4" />
                        Export
                        <ChevronDown className="w-3 h-3" />
                      </>
                    )}
                  </button>
                  {exportMenuOpen && (
                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-10">
                      <button
                        onClick={() => handleCopyContent('text')}
                        className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                      >
                        <Copy className="w-4 h-4" />
                        Copy Plain Text
                      </button>
                      <button
                        onClick={() => handleCopyContent('markdown')}
                        className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                      >
                        <Type className="w-4 h-4" />
                        Copy Markdown
                      </button>
                      <button
                        onClick={() => handleCopyContent('html')}
                        className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                      >
                        <FileCode className="w-4 h-4" />
                        Copy HTML
                      </button>
                      <hr className="my-1 border-gray-200" />
                      <button
                        onClick={handleDownloadJSON}
                        className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                      >
                        <FileJson className="w-4 h-4" />
                        Download JSON
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
            <div className="p-6">
              {/* Enhanced Stats Row with Visual Progress */}
              <div className="grid grid-cols-3 gap-4 mb-6">
                {/* Word Count */}
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-900">{wordCount.toLocaleString()}</div>
                  <div className="text-xs text-gray-500 mb-2">Words</div>
                  <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-secondary-500 rounded-full"
                      style={{ width: `${Math.min((wordCount / 2000) * 100, 100)}%` }}
                    />
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    {wordCount < 300 ? 'Thin content' : wordCount < 1000 ? 'Average' : 'Comprehensive'}
                  </div>
                </div>

                {/* Images with Alt Tag Progress */}
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-900">{imageStats.total}</div>
                  <div className="text-xs text-gray-500 mb-2">Images</div>
                  {imageStats.total > 0 && (
                    <>
                      <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden flex">
                        <div
                          className="h-full bg-green-500"
                          style={{ width: `${(imageStats.withAlt / imageStats.total) * 100}%` }}
                          title={`${imageStats.withAlt} with alt text`}
                        />
                        <div
                          className="h-full bg-red-500"
                          style={{ width: `${(imageStats.missingAlt / imageStats.total) * 100}%` }}
                          title={`${imageStats.missingAlt} missing alt text`}
                        />
                      </div>
                      <div className="text-xs text-gray-400 mt-1">
                        {imageStats.withAlt} good / {imageStats.missingAlt} missing alt
                      </div>
                    </>
                  )}
                </div>

                {/* Missing Alt - Clickable */}
                <button
                  onClick={() => {
                    if (imageStats.missingAlt > 0) {
                      setActiveTab('images');
                      toast.info('Showing images - filter for missing alt text');
                    }
                  }}
                  className={`p-4 rounded-lg text-left transition-all ${
                    imageStats.missingAlt > 0
                      ? 'bg-red-50 hover:bg-red-100 cursor-pointer border-2 border-red-200'
                      : 'bg-green-50 border-2 border-green-200'
                  }`}
                >
                  <div className={`text-2xl font-bold ${imageStats.missingAlt > 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {imageStats.missingAlt}
                  </div>
                  <div className="text-xs text-gray-500 mb-2">Missing Alt</div>
                  {imageStats.missingAlt > 0 ? (
                    <div className="flex items-center gap-1 text-xs text-red-600">
                      <AlertTriangle className="w-3 h-3" />
                      Click to view
                    </div>
                  ) : (
                    <div className="flex items-center gap-1 text-xs text-green-600">
                      <CheckCircle2 className="w-3 h-3" />
                      All images have alt
                    </div>
                  )}
                </button>
              </div>

              {/* Image Thumbnail Strip */}
              {images.length > 0 && (
                <div className="mb-6">
                  <div className="text-sm font-medium text-gray-700 mb-2">Image Preview</div>
                  <div className="relative">
                    {/* Scroll Buttons */}
                    {images.length > 4 && (
                      <>
                        <button
                          onClick={() => scrollThumbnails('left')}
                          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 p-1.5 bg-white/90 hover:bg-white border border-gray-200 rounded-full shadow-sm"
                        >
                          <ChevronLeft className="w-4 h-4 text-gray-600" />
                        </button>
                        <button
                          onClick={() => scrollThumbnails('right')}
                          className="absolute right-0 top-1/2 -translate-y-1/2 z-10 p-1.5 bg-white/90 hover:bg-white border border-gray-200 rounded-full shadow-sm"
                        >
                          <ChevronRight className="w-4 h-4 text-gray-600" />
                        </button>
                      </>
                    )}
                    {/* Thumbnails */}
                    <div
                      ref={thumbnailScrollRef}
                      className="flex gap-2 overflow-x-auto scrollbar-hide px-6"
                      style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
                    >
                      {images.slice(0, 10).map((img, idx) => (
                        <div
                          key={img.id}
                          className={`relative flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border-2 ${
                            img.has_alt ? 'border-gray-200' : 'border-red-300'
                          }`}
                        >
                          <img
                            src={img.src}
                            alt={img.alt || `Image ${idx + 1}`}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="80" height="80"%3E%3Crect fill="%23f3f4f6" width="80" height="80"/%3E%3Ctext fill="%239ca3af" x="50%" y="50%" text-anchor="middle" dy=".3em" font-size="10"%3EError%3C/text%3E%3C/svg%3E';
                            }}
                          />
                          {!img.has_alt && (
                            <div className="absolute top-1 right-1">
                              <span className="flex items-center justify-center w-4 h-4 bg-red-500 rounded-full">
                                <XCircle className="w-3 h-3 text-white" />
                              </span>
                            </div>
                          )}
                        </div>
                      ))}
                      {images.length > 10 && (
                        <button
                          onClick={() => setActiveTab('images')}
                          className="flex-shrink-0 w-20 h-20 rounded-lg bg-gray-100 hover:bg-gray-200 flex items-center justify-center transition-colors"
                        >
                          <span className="text-sm font-medium text-gray-600">+{images.length - 10}</span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Content Preview with Tabs */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-medium text-gray-700">Content Preview</div>
                  <div className="flex border border-gray-200 rounded-md overflow-hidden">
                    <button
                      onClick={() => setContentTab('reader')}
                      className={`px-3 py-1 text-xs font-medium transition-colors ${
                        contentTab === 'reader'
                          ? 'bg-secondary-500 text-white'
                          : 'bg-white text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      Reader View
                    </button>
                    <button
                      onClick={() => setContentTab('raw')}
                      className={`px-3 py-1 text-xs font-medium transition-colors ${
                        contentTab === 'raw'
                          ? 'bg-secondary-500 text-white'
                          : 'bg-white text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      Raw Text
                    </button>
                  </div>
                </div>
                <div className="relative">
                  <div
                    className={`bg-gray-50 rounded-md overflow-hidden transition-all ${
                      contentExpanded ? 'max-h-[600px]' : 'max-h-48'
                    }`}
                  >
                    {contentTab === 'reader' ? (
                      <div className="p-4 prose prose-sm max-w-none">
                        {page.content_summary ? (
                          formatReaderContent(page.content_summary).split('\n\n').map((paragraph, idx) => (
                            <p key={idx} className="text-sm text-gray-700 mb-3 last:mb-0">
                              {paragraph}
                            </p>
                          ))
                        ) : (
                          <p className="text-sm text-gray-400 italic">No content available</p>
                        )}
                      </div>
                    ) : (
                      <pre className="p-4 text-xs text-gray-700 font-mono whitespace-pre-wrap overflow-x-auto">
                        {page.content_summary || 'No content available'}
                      </pre>
                    )}
                  </div>
                  {/* Fade-out Gradient & Expand Button */}
                  {page.content_summary && page.content_summary.length > 300 && !contentExpanded && (
                    <div className="absolute bottom-0 left-0 right-0 h-20 bg-gradient-to-t from-gray-50 to-transparent pointer-events-none" />
                  )}
                </div>
                {page.content_summary && page.content_summary.length > 300 && (
                  <button
                    onClick={() => setContentExpanded(!contentExpanded)}
                    className="mt-2 w-full py-2 text-sm font-medium text-secondary-600 hover:text-secondary-700 hover:bg-gray-50 rounded-md transition-colors flex items-center justify-center gap-1"
                  >
                    {contentExpanded ? (
                      <>
                        <ChevronDown className="w-4 h-4 rotate-180" />
                        Show Less
                      </>
                    ) : (
                      <>
                        <ChevronDown className="w-4 h-4" />
                        Expand Content
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Card 6: Technical Details (Collapsible) */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <button
              onClick={() => setTechnicalExpanded(!technicalExpanded)}
              className="w-full px-6 py-4 bg-gray-50 border-b border-gray-200 flex items-center justify-between hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-center gap-2">
                <Code className="w-5 h-5 text-gray-600" />
                <h2 className="text-lg font-semibold text-gray-900">Technical Details</h2>
              </div>
              {technicalExpanded ? (
                <ChevronDown className="w-5 h-5 text-gray-500" />
              ) : (
                <ChevronRight className="w-5 h-5 text-gray-500" />
              )}
            </button>
            {technicalExpanded && (
              <div className="p-6">
                <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-3 bg-gray-50 rounded-md">
                    <dt className="text-xs font-medium text-gray-500 uppercase">Content Type</dt>
                    <dd className="text-sm text-gray-900 mt-1 font-mono">{page.content_type || 'text/html'}</dd>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-md">
                    <dt className="text-xs font-medium text-gray-500 uppercase">Encoding</dt>
                    <dd className="text-sm text-gray-900 mt-1 font-mono">UTF-8</dd>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-md">
                    <dt className="text-xs font-medium text-gray-500 uppercase">Page ID</dt>
                    <dd className="text-xs text-gray-900 mt-1 font-mono break-all">{page.id}</dd>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-md">
                    <dt className="text-xs font-medium text-gray-500 uppercase">Crawl ID</dt>
                    <dd className="text-xs text-gray-900 mt-1 font-mono break-all">{page.crawl_id}</dd>
                  </div>
                </dl>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Links Tab */}
      {activeTab === 'links' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Links from this Page ({links.length})</h2>
          </div>
          <div className="p-6">
            {links.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                        Target URL
                      </th>
                      <th className="px-4 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                        Anchor Text
                      </th>
                      <th className="px-4 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                        Type
                      </th>
                      <th className="px-4 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {links.map((link) => (
                      <tr key={link.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <a
                            href={link.target_url || link.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-secondary-600 hover:text-secondary-700 truncate max-w-xs block"
                            title={link.target_url || link.url}
                          >
                            {link.target_url || link.url}
                          </a>
                        </td>
                        <td className="px-4 py-3">
                          <div className="text-sm text-gray-900 truncate max-w-xs" title={link.anchor_text}>
                            {link.anchor_text || <span className="text-gray-400">No text</span>}
                          </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            link.is_internal
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-purple-100 text-purple-800'
                          }`}>
                            {link.is_internal ? 'Internal' : 'External'}
                          </span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          {link.is_broken ? (
                            <span className="inline-flex px-2 py-1 text-xs font-semibold text-red-800 bg-red-100 rounded-full">
                              Broken
                            </span>
                          ) : link.status_code ? (
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              link.status_code >= 200 && link.status_code < 300
                                ? 'bg-green-100 text-green-800'
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {link.status_code}
                            </span>
                          ) : (
                            <span className="text-gray-400 text-sm">-</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No links found on this page.</p>
            )}
          </div>
        </div>
      )}

      {/* Images Tab */}
      {activeTab === 'images' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Images on this Page ({images.length})</h2>
              {imageStats.missingAlt > 0 && (
                <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-yellow-800 bg-yellow-100 rounded-full">
                  <AlertTriangle className="w-3 h-3" />
                  {imageStats.missingAlt} missing alt
                </span>
              )}
            </div>
          </div>
          <div className="p-6">
            {images.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {images.map((image) => (
                  <div key={image.id} className="border border-gray-200 rounded-lg overflow-hidden">
                    <div className="aspect-video bg-gray-100 flex items-center justify-center">
                      <img
                        src={image.src}
                        alt={image.alt || 'Image'}
                        className="max-w-full max-h-full object-contain"
                        onError={(e) => {
                          e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Crect fill="%23f3f4f6" width="100" height="100"/%3E%3Ctext fill="%239ca3af" x="50%" y="50%" text-anchor="middle" dy=".3em" font-size="12"%3EFailed to load%3C/text%3E%3C/svg%3E';
                        }}
                      />
                    </div>
                    <div className="p-3">
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <a
                          href={image.src}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-secondary-600 hover:text-secondary-700 truncate flex-1"
                          title={image.src}
                        >
                          {image.src.split('/').pop() || image.src}
                        </a>
                        {image.is_broken ? (
                          <span className="inline-flex px-1.5 py-0.5 text-xs font-semibold text-red-800 bg-red-100 rounded">
                            Broken
                          </span>
                        ) : (
                          <span className="inline-flex px-1.5 py-0.5 text-xs font-semibold text-green-800 bg-green-100 rounded">
                            OK
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-xs">
                        {image.has_alt ? (
                          <span className="text-gray-600 truncate" title={image.alt}>
                            Alt: {image.alt || 'Empty'}
                          </span>
                        ) : (
                          <span className="text-red-600 flex items-center gap-1">
                            <XCircle className="w-3 h-3" /> Missing alt text
                          </span>
                        )}
                      </div>
                      {image.width && image.height && (
                        <div className="text-xs text-gray-500 mt-1">
                          {image.width} x {image.height}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No images found on this page.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default PageDetailPage;
