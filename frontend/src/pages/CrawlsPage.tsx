import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiService, Crawl, CrawlCreate } from '../services/api';

const CrawlsPage: React.FC = () => {
  const [crawls, setCrawls] = useState<Crawl[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState<CrawlCreate>({
    url: '',
    name: '',
    max_depth: 2,
    max_pages: 100,
    respect_robots_txt: true,
    follow_external_links: false,
    js_rendering: false,
    rate_limit: 1,
    user_agent: 'AAA Web Scraper Bot'
  });
  const [formSubmitting, setFormSubmitting] = useState(false);

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
      setError('Failed to load crawls. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormSubmitting(true);
    setError(null);

    try {
      await apiService.createCrawl(formData);
      setShowCreateForm(false);
      setFormData({
        url: '',
        name: '',
        max_depth: 2,
        max_pages: 100,
        respect_robots_txt: true,
        follow_external_links: false,
        js_rendering: false,
        rate_limit: 1,
        user_agent: 'AAA Web Scraper Bot'
      });
      fetchCrawls();
    } catch (err) {
      console.error('Error creating crawl:', err);
      setError('Failed to create crawl. Please check your inputs and try again.');
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this crawl? This action cannot be undone.')) {
      return;
    }

    try {
      await apiService.deleteCrawl(id);
      setCrawls(crawls.filter(crawl => crawl.id !== id));
    } catch (err) {
      console.error('Error deleting crawl:', err);
      setError('Failed to delete crawl. Please try again later.');
    }
  };

  const handleDeleteFailedCrawls = async () => {
    const failedCrawls = crawls.filter(crawl => crawl.status === 'failed');
    
    if (failedCrawls.length === 0) {
      setError('No failed crawls to delete.');
      return;
    }

    if (!window.confirm(`Are you sure you want to delete ${failedCrawls.length} failed crawl(s)? This action cannot be undone.`)) {
      return;
    }

    try {
      setFormSubmitting(true);
      
      // Delete failed crawls one by one to identify which one fails
      const results = [];
      for (const crawl of failedCrawls) {
        try {
          await apiService.deleteCrawl(crawl.id);
          results.push({ id: crawl.id, success: true });
        } catch (err) {
          console.error(`Error deleting crawl ${crawl.id}:`, err);
          results.push({ id: crawl.id, success: false, error: err });
        }
      }
      
      // Update local state - remove successfully deleted crawls
      const successfullyDeleted = results.filter(r => r.success).map(r => r.id);
      setCrawls(crawls.filter(crawl => !successfullyDeleted.includes(crawl.id)));
      
      const failedCount = results.filter(r => !r.success).length;
      if (failedCount > 0) {
        setError(`Failed to delete ${failedCount} crawl(s). Check console for details.`);
      }
      
    } catch (err) {
      console.error('Error deleting failed crawls:', err);
      setError('Failed to delete failed crawls. Please try again later.');
    } finally {
      setFormSubmitting(false);
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

  return (
    <div className="container px-4 py-8 mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Website Crawls</h1>
        <div className="flex space-x-3">
          {crawls.filter(crawl => crawl.status === 'failed').length > 0 && (
            <button
              onClick={handleDeleteFailedCrawls}
              disabled={formSubmitting}
              className="px-4 py-2 text-white bg-red-600 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
            >
              {formSubmitting ? 'Deleting...' : `Delete ${crawls.filter(crawl => crawl.status === 'failed').length} Failed`}
            </button>
          )}
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="px-4 py-2 text-white bg-indigo-600 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            {showCreateForm ? 'Cancel' : 'New Crawl'}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 mb-6 text-sm text-red-700 bg-red-100 rounded-md" role="alert">
          {error}
        </div>
      )}

      {showCreateForm && (
        <div className="p-6 mb-6 bg-white rounded-lg shadow">
          <h2 className="mb-4 text-xl font-semibold text-gray-800">Create New Crawl</h2>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                  Crawl Name
                </label>
                <input
                  type="text"
                  name="name"
                  id="name"
                  required
                  value={formData.name}
                  onChange={handleInputChange}
                  className="block w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div>
                <label htmlFor="start_url" className="block text-sm font-medium text-gray-700">
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
                  className="block w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div>
                <label htmlFor="max_depth" className="block text-sm font-medium text-gray-700">
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
                  className="block w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div>
                <label htmlFor="max_pages" className="block text-sm font-medium text-gray-700">
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
                  className="block w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div>
                <label htmlFor="rate_limit" className="block text-sm font-medium text-gray-700">
                  Rate Limit (requests per second)
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
                  className="block w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div>
                <label htmlFor="user_agent" className="block text-sm font-medium text-gray-700">
                  User Agent
                </label>
                <input
                  type="text"
                  name="user_agent"
                  id="user_agent"
                  value={formData.user_agent || ''}
                  onChange={handleInputChange}
                  className="block w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div className="flex items-center mt-4">
                <input
                  type="checkbox"
                  name="respect_robots_txt"
                  id="respect_robots_txt"
                  checked={formData.respect_robots_txt}
                  onChange={handleInputChange}
                  className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                />
                <label htmlFor="respect_robots_txt" className="block ml-2 text-sm text-gray-700">
                  Respect robots.txt
                </label>
              </div>

              <div className="flex items-center mt-4">
                <input
                  type="checkbox"
                  name="follow_external_links"
                  id="follow_external_links"
                  checked={formData.follow_external_links}
                  onChange={handleInputChange}
                  className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                />
                <label htmlFor="follow_external_links" className="block ml-2 text-sm text-gray-700">
                  Follow external links
                </label>
              </div>

              <div className="flex items-center mt-4">
                <input
                  type="checkbox"
                  name="js_rendering"
                  id="js_rendering"
                  checked={formData.js_rendering}
                  onChange={handleInputChange}
                  className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                />
                <label htmlFor="js_rendering" className="block ml-2 text-sm text-gray-700">
                  Enable JavaScript rendering
                </label>
              </div>
            </div>

            <div className="mt-6">
              <button
                type="submit"
                disabled={formSubmitting}
                className="inline-flex justify-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                {formSubmitting ? 'Creating...' : 'Create Crawl'}
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-lg font-medium text-gray-500">Loading crawls...</div>
        </div>
      ) : crawls.length > 0 ? (
        <div className="overflow-hidden bg-white shadow sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {crawls.map((crawl) => (
              <li key={crawl.id}>
                <div className="px-4 py-4 sm:px-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <p className="text-lg font-medium text-indigo-600 truncate">
                        <Link to={`/crawls/${crawl.id}`}>{crawl.name}</Link>
                      </p>
                      <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeClass(crawl.status)}`}>
                        {crawl.status}
                      </span>
                    </div>
                    <div className="flex">
                      <Link
                        to={`/crawls/${crawl.id}`}
                        className="inline-flex items-center px-3 py-1 text-sm font-medium text-indigo-600 bg-indigo-100 rounded-md hover:bg-indigo-200"
                      >
                        View
                      </Link>
                      <button
                        onClick={() => handleDelete(crawl.id)}
                        className="inline-flex items-center px-3 py-1 ml-2 text-sm font-medium text-red-600 bg-red-100 rounded-md hover:bg-red-200"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                  <div className="mt-2 sm:flex sm:justify-between">
                    <div className="sm:flex">
                      <p className="flex items-center text-sm text-gray-500">
                        <svg className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clipRule="evenodd" />
                        </svg>
                        {crawl.url.length > 40 ? `${crawl.url.substring(0, 40)}...` : crawl.url}
                      </p>
                      <p className="flex items-center mt-2 text-sm text-gray-500 sm:mt-0 sm:ml-6">
                        <svg className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                          <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
                        </svg>
                        Depth: {crawl.max_depth}, Max Pages: {crawl.max_pages}
                      </p>
                    </div>
                    <div className="flex items-center mt-2 text-sm text-gray-500 sm:mt-0">
                      <svg className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                      </svg>
                      <span>Created: {formatDate(crawl.created_at)}</span>
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <div className="p-6 text-center bg-white rounded-lg shadow">
          <p className="text-gray-500">No crawls found. Create your first crawl to get started.</p>
          <button
            onClick={() => setShowCreateForm(true)}
            className="px-4 py-2 mt-4 text-white bg-indigo-600 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Create First Crawl
          </button>
        </div>
      )}
    </div>
  );
};

export default CrawlsPage;
