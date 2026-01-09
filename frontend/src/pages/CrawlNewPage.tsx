import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { ArrowLeft, Loader2, Plus } from 'lucide-react';
import { apiService, CrawlCreate } from '../services/api';

const CrawlNewPage: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<CrawlCreate>({
    url: '',
    name: '',
    max_depth: 2,
    max_pages: 100,
    respect_robots_txt: true,
    follow_external_links: false,
    js_rendering: false,
    rate_limit: 1,
    user_agent: 'AI WebScraper Bot'
  });
  const [formSubmitting, setFormSubmitting] = useState(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target as HTMLInputElement;

    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox'
        ? (e.target as HTMLInputElement).checked
        : type === 'number'
          ? Number(value)
          : value
    }));
  };

  const validateForm = (): string | null => {
    if (!formData.url || !formData.url.startsWith('http')) {
      return 'Please enter a valid URL starting with http:// or https://';
    }
    if (!formData.name || formData.name.trim().length === 0) {
      return 'Please enter a crawl name';
    }
    if (formData.max_depth < 1 || formData.max_depth > 10) {
      return 'Max depth must be between 1 and 10';
    }
    if (formData.max_pages < 1 || formData.max_pages > 1000) {
      return 'Max pages must be between 1 and 1000';
    }
    if (formData.rate_limit < 0.1 || formData.rate_limit > 10) {
      return 'Rate limit must be between 0.1 and 10 requests per second';
    }
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate form before submission
    const validationError = validateForm();
    if (validationError) {
      toast.error(validationError);
      return;
    }

    setFormSubmitting(true);

    try {
      await apiService.createCrawl(formData);
      toast.success('Crawl created successfully');
      navigate('/crawls');
    } catch (err: any) {
      console.error('Error creating crawl:', err);
      const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to create crawl';
      toast.error(errorMessage);
    } finally {
      setFormSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto" style={{ padding: '4rem 2rem' }}>
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate('/crawls')}
          className="inline-flex items-center gap-2 mb-4 text-sm font-medium text-neutral-steel hover:text-secondary-600 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Crawls
        </button>
        <h1 className="text-3xl font-semibold text-neutral-charcoal">Create New Crawl</h1>
        <p className="mt-2 text-base text-neutral-steel leading-comfortable">
          Configure your website crawl settings
        </p>
      </div>

      {/* Form */}
      <div className="bg-white rounded-lg shadow-soft-lg border border-primary-100 overflow-hidden">
        <form onSubmit={handleSubmit} style={{ padding: '2.5rem' }}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="name" className="block text-sm font-semibold text-neutral-charcoal mb-2">
                Crawl Name
              </label>
              <input
                type="text"
                name="name"
                id="name"
                required
                value={formData.name}
                onChange={handleInputChange}
                placeholder="My Website Audit"
                className="block w-full px-4 py-3 border border-primary-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-secondary-500 focus:border-secondary-500 text-sm text-neutral-charcoal"
              />
            </div>

            <div>
              <label htmlFor="url" className="block text-sm font-semibold text-neutral-charcoal mb-2">
                Start URL
              </label>
              <input
                type="url"
                name="url"
                id="url"
                required
                value={formData.url}
                onChange={handleInputChange}
                placeholder="https://example.com"
                className="block w-full px-4 py-3 border border-primary-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-secondary-500 focus:border-secondary-500 text-sm text-neutral-charcoal"
              />
            </div>

            <div>
              <label htmlFor="max_depth" className="block text-sm font-semibold text-neutral-charcoal mb-2">
                Max Depth
              </label>
              <input
                type="number"
                name="max_depth"
                id="max_depth"
                min="1"
                max="10"
                required
                value={formData.max_depth}
                onChange={handleInputChange}
                className="block w-full px-4 py-3 border border-primary-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-secondary-500 focus:border-secondary-500 text-sm text-neutral-charcoal"
              />
              <p className="mt-1.5 text-xs text-neutral-steel">How many levels deep to crawl (1-10)</p>
            </div>

            <div>
              <label htmlFor="max_pages" className="block text-sm font-semibold text-neutral-charcoal mb-2">
                Max Pages
              </label>
              <input
                type="number"
                name="max_pages"
                id="max_pages"
                min="1"
                max="1000"
                required
                value={formData.max_pages}
                onChange={handleInputChange}
                className="block w-full px-4 py-3 border border-primary-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-secondary-500 focus:border-secondary-500 text-sm text-neutral-charcoal"
              />
              <p className="mt-1.5 text-xs text-neutral-steel">Maximum number of pages to crawl</p>
            </div>

            <div>
              <label htmlFor="rate_limit" className="block text-sm font-semibold text-neutral-charcoal mb-2">
                Rate Limit
              </label>
              <input
                type="number"
                name="rate_limit"
                id="rate_limit"
                min="0.1"
                max="10"
                step="0.1"
                required
                value={formData.rate_limit}
                onChange={handleInputChange}
                className="block w-full px-4 py-3 border border-primary-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-secondary-500 focus:border-secondary-500 text-sm text-neutral-charcoal"
              />
              <p className="mt-1.5 text-xs text-neutral-steel">Requests per second (0.1-10)</p>
            </div>

            <div>
              <label htmlFor="user_agent" className="block text-sm font-semibold text-neutral-charcoal mb-2">
                User Agent
              </label>
              <input
                type="text"
                name="user_agent"
                id="user_agent"
                value={formData.user_agent || ''}
                onChange={handleInputChange}
                className="block w-full px-4 py-3 border border-primary-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-secondary-500 focus:border-secondary-500 text-sm text-neutral-charcoal"
              />
              <p className="mt-1.5 text-xs text-neutral-steel">Custom user agent string</p>
            </div>
          </div>

          <div className="mt-8 space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                name="respect_robots_txt"
                id="respect_robots_txt"
                checked={formData.respect_robots_txt}
                onChange={handleInputChange}
                className="w-4 h-4 text-secondary-500 border-primary-300 rounded focus:ring-secondary-500"
              />
              <label htmlFor="respect_robots_txt" className="ml-3 text-sm text-neutral-charcoal">
                Respect robots.txt
              </label>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                name="follow_external_links"
                id="follow_external_links"
                checked={formData.follow_external_links}
                onChange={handleInputChange}
                className="w-4 h-4 text-secondary-500 border-primary-300 rounded focus:ring-secondary-500"
              />
              <label htmlFor="follow_external_links" className="ml-3 text-sm text-neutral-charcoal">
                Follow external links
              </label>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                name="js_rendering"
                id="js_rendering"
                checked={formData.js_rendering}
                onChange={handleInputChange}
                className="w-4 h-4 text-secondary-500 border-primary-300 rounded focus:ring-secondary-500"
              />
              <label htmlFor="js_rendering" className="ml-3 text-sm text-neutral-charcoal">
                Enable JavaScript rendering
              </label>
            </div>
          </div>

          <div className="mt-8 flex items-center gap-4">
            <button
              type="submit"
              disabled={formSubmitting}
              className="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium text-white bg-secondary-500 hover:bg-secondary-hover rounded-lg shadow-soft transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {formSubmitting ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Creating Crawl...
                </>
              ) : (
                <>
                  <Plus className="w-5 h-5" />
                  Create Crawl
                </>
              )}
            </button>
            <button
              type="button"
              onClick={() => navigate('/crawls')}
              disabled={formSubmitting}
              className="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium text-neutral-steel bg-white hover:bg-primary-50 border border-primary-200 rounded-lg shadow-soft transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CrawlNewPage;