import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { toast } from 'sonner';
import { Image as ImageIcon, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

interface ImageAnalysis {
  id: string;
  page_id: string;
  crawl_id: string;
  image_url: string;
  current_alt: string | null;
  suggested_alt: string;
  is_decorative: boolean;
  confidence: number;
  context: string | null;
  created_at: string;
}

interface PageInfo {
  id: string;
  url: string;
  title: string;
}

const ImagesPage: React.FC = () => {
  const { crawlId } = useParams<{ crawlId: string }>();
  const [images, setImages] = useState<ImageAnalysis[]>([]);
  const [pages, setPages] = useState<Map<string, PageInfo>>(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'missing' | 'poor'>('all');

  useEffect(() => {
    fetchImageAnalysis();
  }, [crawlId]);

  const fetchImageAnalysis = async () => {
    if (!crawlId) return;
    
    try {
      setLoading(true);
      setError(null);

      // TODO: Replace with actual API call when backend endpoint is ready
      // const response = await apiService.getImageAnalysis(crawlId);
      // setImages(response.images);
      // setPages(new Map(response.pages.map(p => [p.id, p])));

      // Mock data for now
      setImages([]);
      setPages(new Map());
      
    } catch (err) {
      console.error('Error fetching image analysis:', err);
      setError('Failed to load image analysis data');
      toast.error('Failed to load images');
    } finally {
      setLoading(false);
    }
  };

  const getFilteredImages = () => {
    switch (filter) {
      case 'missing':
        return images.filter(img => !img.current_alt || img.current_alt.trim() === '');
      case 'poor':
        return images.filter(img => img.confidence < 0.7 || (img.current_alt && img.current_alt.length < 10));
      default:
        return images;
    }
  };

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.9) {
      return <span className="inline-flex items-center px-2 py-1 text-xs font-medium text-green-700 bg-green-100 rounded-full">
        <CheckCircle className="w-3 h-3 mr-1" />
        High
      </span>;
    } else if (confidence >= 0.7) {
      return <span className="inline-flex items-center px-2 py-1 text-xs font-medium text-yellow-700 bg-yellow-100 rounded-full">
        <AlertCircle className="w-3 h-3 mr-1" />
        Medium
      </span>;
    } else {
      return <span className="inline-flex items-center px-2 py-1 text-xs font-medium text-red-700 bg-red-100 rounded-full">
        <XCircle className="w-3 h-3 mr-1" />
        Low
      </span>;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg font-medium text-gray-500">Loading image analysis...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container px-4 py-8 mx-auto">
        <div className="p-4 mb-6 text-sm text-red-700 bg-red-100 rounded-md" role="alert">
          {error}
        </div>
        <Link to={`/crawls/${crawlId}`} className="text-secondary-500 hover:text-secondary-600">
          &larr; Back to Crawl
        </Link>
      </div>
    );
  }

  const filteredImages = getFilteredImages();
  const missingAltCount = images.filter(img => !img.current_alt || img.current_alt.trim() === '').length;
  const poorQualityCount = images.filter(img => img.confidence < 0.7).length;

  return (
    <div className="container px-4 py-8 mx-auto">
      <div className="mb-6">
        <Link to={`/crawls/${crawlId}`} className="text-secondary-500 hover:text-secondary-600">
          &larr; Back to Crawl
        </Link>
      </div>

      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Image Analysis</h1>
            <p className="mt-2 text-gray-600">AI-generated alt text suggestions for images</p>
          </div>
          <div className="flex items-center gap-3">
            <ImageIcon className="w-8 h-8 text-secondary-500" />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 mt-6 sm:grid-cols-3">
          <div className="p-4 bg-white border border-gray-200 rounded-lg shadow-sm">
            <div className="text-sm text-gray-500">Total Images</div>
            <div className="mt-1 text-2xl font-semibold text-gray-900">{images.length}</div>
          </div>
          <div className="p-4 bg-white border border-gray-200 rounded-lg shadow-sm">
            <div className="text-sm text-gray-500">Missing Alt Text</div>
            <div className="mt-1 text-2xl font-semibold text-red-600">{missingAltCount}</div>
          </div>
          <div className="p-4 bg-white border border-gray-200 rounded-lg shadow-sm">
            <div className="text-sm text-gray-500">Poor Quality</div>
            <div className="mt-1 text-2xl font-semibold text-yellow-600">{poorQualityCount}</div>
          </div>
        </div>
      </div>

      <div className="mb-6">
        <div className="flex gap-2">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 text-sm font-medium rounded-md ${
              filter === 'all'
                ? 'bg-secondary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All Images ({images.length})
          </button>
          <button
            onClick={() => setFilter('missing')}
            className={`px-4 py-2 text-sm font-medium rounded-md ${
              filter === 'missing'
                ? 'bg-secondary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Missing Alt ({missingAltCount})
          </button>
          <button
            onClick={() => setFilter('poor')}
            className={`px-4 py-2 text-sm font-medium rounded-md ${
              filter === 'poor'
                ? 'bg-secondary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Poor Quality ({poorQualityCount})
          </button>
        </div>
      </div>

      {filteredImages.length === 0 ? (
        <div className="p-8 text-center bg-white border border-gray-200 rounded-lg">
          <ImageIcon className="w-12 h-12 mx-auto text-gray-400" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">No images found</h3>
          <p className="mt-2 text-sm text-gray-500">
            {filter === 'all' 
              ? 'No images have been analyzed for this crawl yet.'
              : `No images match the "${filter}" filter.`}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredImages.map((image) => {
            const page = pages.get(image.page_id);
            
            return (
              <div key={image.id} className="p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
                <div className="flex gap-6">
                  <div className="flex-shrink-0">
                    <div className="w-32 h-32 overflow-hidden bg-gray-100 border border-gray-200 rounded-lg">
                      <img
                        src={image.image_url}
                        alt={image.current_alt || 'Image preview'}
                        className="object-cover w-full h-full"
                        onError={(e) => {
                          (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="128" height="128"%3E%3Crect fill="%23f3f4f6" width="128" height="128"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" fill="%239ca3af" font-size="14"%3ENo Image%3C/text%3E%3C/svg%3E';
                        }}
                      />
                    </div>
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="text-sm font-medium text-gray-900 truncate">
                            {image.image_url}
                          </h3>
                          {getConfidenceBadge(image.confidence)}
                          {image.is_decorative && (
                            <span className="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-700 bg-gray-100 rounded-full">
                              Decorative
                            </span>
                          )}
                        </div>
                        
                        {page && (
                          <div className="mb-3 text-sm text-gray-500">
                            <span className="font-medium">Page:</span>{' '}
                            <Link 
                              to={`/pages/${page.id}`}
                              className="text-secondary-500 hover:text-secondary-600 hover:underline"
                            >
                              {page.title || page.url}
                            </Link>
                          </div>
                        )}

                        <div className="space-y-3">
                          <div>
                            <div className="text-xs font-medium text-gray-500 uppercase">Current Alt Text</div>
                            <div className="mt-1 text-sm text-gray-900">
                              {image.current_alt || (
                                <span className="italic text-red-600">Missing</span>
                              )}
                            </div>
                          </div>

                          <div>
                            <div className="text-xs font-medium text-gray-500 uppercase">AI Suggested Alt Text</div>
                            <div className="mt-1 text-sm font-medium text-green-700">
                              {image.suggested_alt}
                            </div>
                          </div>

                          {image.context && (
                            <div>
                              <div className="text-xs font-medium text-gray-500 uppercase">Context</div>
                              <div className="mt-1 text-sm text-gray-600">{image.context}</div>
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="flex flex-col gap-2 ml-4">
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(image.suggested_alt);
                            toast.success('Alt text copied to clipboard');
                          }}
                          className="px-3 py-1 text-xs font-medium text-white bg-secondary-600 rounded-md hover:bg-secondary-700"
                        >
                          Copy
                        </button>
                        <button
                          onClick={() => {
                            window.open(image.image_url, '_blank');
                          }}
                          className="px-3 py-1 text-xs font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                        >
                          View
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ImagesPage;
