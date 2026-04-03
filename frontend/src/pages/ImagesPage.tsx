import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { toast } from 'sonner';
import { Image as ImageIcon, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { usePageTitle } from '../hooks/usePageTitle';
import { apiService, Image } from '../services/api';

const ImagesPage: React.FC = () => {
  usePageTitle('Images');

  const { crawlId } = useParams<{ crawlId: string }>();
  const [images, setImages] = useState<Image[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'missing_alt' | 'broken'>('all');

  const fetchImages = useCallback(async () => {
    if (!crawlId) return;

    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getCrawlImages(crawlId);
      setImages(data);
    } catch (err) {
      console.error('Error fetching images:', err);
      setError('Failed to load image data');
      toast.error('Failed to load images');
    } finally {
      setLoading(false);
    }
  }, [crawlId]);

  useEffect(() => {
    fetchImages();
  }, [fetchImages]);

  const getFilteredImages = () => {
    switch (filter) {
      case 'missing_alt':
        return images.filter(img => !img.has_alt);
      case 'broken':
        return images.filter(img => img.is_broken);
      default:
        return images;
    }
  };

  const missingAltCount = images.filter(img => !img.has_alt).length;
  const brokenCount = images.filter(img => img.is_broken).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-secondary-500"></div>
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
            <h1 className="text-3xl font-bold text-gray-900">Images</h1>
            <p className="mt-2 text-gray-600">All images discovered during this crawl</p>
          </div>
          <ImageIcon className="w-8 h-8 text-secondary-500" />
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
            <div className="text-sm text-gray-500">Broken Images</div>
            <div className="mt-1 text-2xl font-semibold text-yellow-600">{brokenCount}</div>
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
            All ({images.length})
          </button>
          <button
            onClick={() => setFilter('missing_alt')}
            className={`px-4 py-2 text-sm font-medium rounded-md ${
              filter === 'missing_alt'
                ? 'bg-secondary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Missing Alt ({missingAltCount})
          </button>
          <button
            onClick={() => setFilter('broken')}
            className={`px-4 py-2 text-sm font-medium rounded-md ${
              filter === 'broken'
                ? 'bg-secondary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Broken ({brokenCount})
          </button>
        </div>
      </div>

      {filteredImages.length === 0 ? (
        <div className="p-8 text-center bg-white border border-gray-200 rounded-lg">
          <ImageIcon className="w-12 h-12 mx-auto text-gray-400" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">No images found</h3>
          <p className="mt-2 text-sm text-gray-500">
            {filter === 'all'
              ? 'No images were discovered during this crawl.'
              : `No images match the "${filter.replace('_', ' ')}" filter.`}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredImages.map((image) => (
            <div key={image.id} className="p-4 bg-white border border-gray-200 rounded-lg shadow-sm">
              <div className="flex gap-4">
                <div className="flex-shrink-0">
                  <div className="w-24 h-24 overflow-hidden bg-gray-100 border border-gray-200 rounded-lg">
                    <img
                      src={image.src}
                      alt={image.alt || 'Image preview'}
                      loading="lazy"
                      width={96}
                      height={96}
                      className="object-cover w-full h-full"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="96" height="96"%3E%3Crect fill="%23f3f4f6" width="96" height="96"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" fill="%239ca3af" font-size="12"%3ENo Image%3C/text%3E%3C/svg%3E';
                      }}
                    />
                  </div>
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="text-sm font-medium text-gray-900 truncate">{image.src}</p>
                    {image.is_broken ? (
                      <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium text-red-700 bg-red-100 rounded-full">
                        <XCircle className="w-3 h-3 mr-1" />
                        Broken{image.status_code ? ` (${image.status_code})` : ''}
                      </span>
                    ) : !image.has_alt ? (
                      <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium text-yellow-700 bg-yellow-100 rounded-full">
                        <AlertTriangle className="w-3 h-3 mr-1" />
                        No Alt
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium text-green-700 bg-green-100 rounded-full">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        OK
                      </span>
                    )}
                  </div>

                  {image.alt && (
                    <p className="text-sm text-gray-600 mt-1">
                      <span className="font-medium text-gray-500">Alt:</span> {image.alt}
                    </p>
                  )}

                  {image.error && (
                    <p className="text-sm text-red-600 mt-1">{image.error}</p>
                  )}

                  {image.width && image.height && (
                    <p className="text-xs text-gray-400 mt-1">{image.width} x {image.height}</p>
                  )}
                </div>

                <div className="flex-shrink-0">
                  <a
                    href={image.src}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3 py-1 text-xs font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                  >
                    Open
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ImagesPage;
