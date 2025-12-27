import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, ExternalLink, Copy, Check } from 'lucide-react';
import { toast } from 'sonner';
import { apiService } from '../services/api';

interface PageData {
  id: string;
  crawl_id: string;
  url: string;
  title: string;
  meta_description: string | null;
  content_summary: string;
  status_code: number;
  response_time: number;
  content_type: string;
  content_length: number;
  h1_tags: string[];
  h2_tags: string[];
  internal_links: number;
  external_links: number;
  images: number;
  created_at: string;
}

const PageDetailPage: React.FC = () => {
  const { crawlId, pageId } = useParams<{ crawlId: string; pageId: string }>();
  const [page, setPage] = useState<PageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchPageData();
  }, [pageId]);

  const fetchPageData = async () => {
    if (!crawlId || !pageId) return;

    try {
      setLoading(true);
      const data = await apiService.getPageDetail(crawlId, pageId);
      setPage(data);
    } catch (err) {
      console.error('Error fetching page:', err);
      toast.error('Failed to load page data');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyContent = () => {
    if (page?.content_summary) {
      navigator.clipboard.writeText(page.content_summary);
      setCopied(true);
      toast.success('Content copied to clipboard');
      setTimeout(() => setCopied(false), 2000);
    }
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

  return (
    <div className="container px-4 py-8 mx-auto max-w-6xl">
      <div className="mb-6">
        <Link to={`/crawls/${crawlId}`} className="inline-flex items-center gap-2 text-secondary-500 hover:text-secondary-600">
          <ArrowLeft className="w-4 h-4" />
          Back to Crawl
        </Link>
      </div>

      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">{page.title}</h1>
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <a 
            href={page.url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-secondary-500 hover:text-secondary-600"
          >
            {page.url}
            <ExternalLink className="w-4 h-4" />
          </a>
          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
            page.status_code >= 200 && page.status_code < 300
              ? 'bg-green-100 text-green-800'
              : 'bg-red-100 text-red-800'
          }`}>
            {page.status_code}
          </span>
        </div>
      </div>

      {/* Page Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm text-gray-500">Response Time</div>
          <div className="text-2xl font-semibold text-gray-900">{page.response_time}ms</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm text-gray-500">Content Size</div>
          <div className="text-2xl font-semibold text-gray-900">{(page.content_length / 1024).toFixed(1)}KB</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm text-gray-500">Internal Links</div>
          <div className="text-2xl font-semibold text-gray-900">{page.internal_links}</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm text-gray-500">External Links</div>
          <div className="text-2xl font-semibold text-gray-900">{page.external_links}</div>
        </div>
      </div>

      {/* Meta Description */}
      {page.meta_description && (
        <div className="bg-white rounded-lg shadow mb-6 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Meta Description</h2>
          <p className="text-gray-700">{page.meta_description}</p>
        </div>
      )}

      {/* Page Content */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Page Content</h2>
          <button
            onClick={handleCopyContent}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                Copy Content
              </>
            )}
          </button>
        </div>
        <div className="prose max-w-none">
          <pre className="whitespace-pre-wrap text-sm text-gray-700 bg-gray-50 p-4 rounded-md overflow-x-auto">
            {page.content_summary || 'No content available'}
          </pre>
        </div>
      </div>

      {/* Headings */}
      {(page.h1_tags.length > 0 || page.h2_tags.length > 0) && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Page Structure</h2>
          
          {page.h1_tags.length > 0 && (
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-700 mb-2">H1 Tags</h3>
              <ul className="list-disc list-inside space-y-1">
                {page.h1_tags.map((tag, idx) => (
                  <li key={idx} className="text-sm text-gray-600">{tag}</li>
                ))}
              </ul>
            </div>
          )}
          
          {page.h2_tags.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">H2 Tags</h3>
              <ul className="list-disc list-inside space-y-1">
                {page.h2_tags.map((tag, idx) => (
                  <li key={idx} className="text-sm text-gray-600">{tag}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Technical Details */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Technical Details</h2>
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <dt className="text-sm font-medium text-gray-500">Content Type</dt>
            <dd className="text-sm text-gray-900">{page.content_type}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Images</dt>
            <dd className="text-sm text-gray-900">{page.images}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Crawled At</dt>
            <dd className="text-sm text-gray-900">{new Date(page.created_at).toLocaleString()}</dd>
          </div>
        </dl>
      </div>
    </div>
  );
};

export default PageDetailPage;
