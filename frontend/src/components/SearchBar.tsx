import React, { useState, useEffect } from 'react';
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { apiService, Page, Link, Image } from '../services/api';

interface SearchBarProps {
  crawlId: string;
  onResultsChange?: (results: SearchResults | null) => void;
}

interface SearchResults {
  query: string;
  results: {
    pages: Page[];
    links: Link[];
    images: Image[];
  };
  counts: {
    pages: number;
    links: number;
    images: number;
  };
}

export default function SearchBar({ crawlId, onResultsChange }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResults | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const handleSearch = async (searchQuery: string) => {
    if (searchQuery.length < 2) {
      setSearchResults(null);
      setShowResults(false);
      if (onResultsChange) onResultsChange(null);
      return;
    }

    setIsSearching(true);
    try {
      const results = await apiService.searchCrawlData(crawlId, searchQuery);
      setSearchResults(results);
      setShowResults(true);
      if (onResultsChange) onResultsChange(results);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  };

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (query) {
        handleSearch(query);
      }
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [query]);

  const handleClear = () => {
    setQuery('');
    setSearchResults(null);
    setShowResults(false);
    if (onResultsChange) onResultsChange(null);
  };

  const totalResults = searchResults
    ? searchResults.counts.pages + searchResults.counts.links + searchResults.counts.images
    : 0;

  return (
    <div className="relative w-full max-w-2xl">
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
        </div>
        <input
          type="text"
          className="block w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
          placeholder="Search pages, links, images..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        {query && (
          <button
            onClick={handleClear}
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
          >
            <XMarkIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
          </button>
        )}
      </div>

      {isSearching && (
        <div className="absolute mt-2 w-full bg-white rounded-lg shadow-lg border border-gray-200 p-4">
          <p className="text-gray-500">Searching...</p>
        </div>
      )}

      {showResults && searchResults && !isSearching && (
        <div className="absolute mt-2 w-full bg-white rounded-lg shadow-lg border border-gray-200 max-h-96 overflow-y-auto z-10">
          <div className="p-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-sm font-semibold text-gray-700">
                Search Results ({totalResults})
              </h3>
              <button
                onClick={() => setShowResults(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>

            {totalResults === 0 ? (
              <p className="text-gray-500 text-sm">No results found</p>
            ) : (
              <div className="space-y-4">
                {searchResults.counts.pages > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-gray-600 uppercase mb-2">
                      Pages ({searchResults.counts.pages})
                    </h4>
                    <div className="space-y-2">
                      {searchResults.results.pages.slice(0, 5).map((page) => (
                        <div key={page.id} className="text-sm">
                          <a
                            href={page.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline font-medium"
                          >
                            {page.title || 'Untitled'}
                          </a>
                          <p className="text-gray-500 text-xs truncate">{page.url}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {searchResults.counts.links > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-gray-600 uppercase mb-2">
                      Links ({searchResults.counts.links})
                    </h4>
                    <div className="space-y-2">
                      {searchResults.results.links.slice(0, 5).map((link) => (
                        <div key={link.id} className="text-sm">
                          <p className="text-gray-700">{link.anchor_text || 'No anchor text'}</p>
                          <p className="text-gray-500 text-xs truncate">{link.target_url}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {searchResults.counts.images > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-gray-600 uppercase mb-2">
                      Images ({searchResults.counts.images})
                    </h4>
                    <div className="space-y-2">
                      {searchResults.results.images.slice(0, 5).map((image) => (
                        <div key={image.id} className="text-sm flex items-center gap-2">
                          <img
                            src={image.src}
                            alt={image.alt || 'No alt text'}
                            className="w-12 h-12 object-cover rounded"
                            onError={(e) => {
                              (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Crect fill="%23ddd" width="100" height="100"/%3E%3C/svg%3E';
                            }}
                          />
                          <div className="flex-1 min-w-0">
                            <p className="text-gray-700 truncate">{image.alt || 'No alt text'}</p>
                            <p className="text-gray-500 text-xs truncate">{image.src}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
