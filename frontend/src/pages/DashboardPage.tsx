import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiService, Crawl } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { Globe, CheckCircle, XCircle, Clock, TrendingUp, Activity } from 'lucide-react';

interface DashboardStats {
  totalCrawls: number;
  completedCrawls: number;
  failedCrawls: number;
  activeCrawls: number;
  totalPages: number;
}

const DashboardPage: React.FC = () => {
  const [recentCrawls, setRecentCrawls] = useState<Crawl[]>([]);
  const [stats, setStats] = useState<DashboardStats>({
    totalCrawls: 0,
    completedCrawls: 0,
    failedCrawls: 0,
    activeCrawls: 0,
    totalPages: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        
        // Fetch all crawls to calculate stats
        const crawls = await apiService.getCrawls();
        
        // Sort by created_at descending and get top 5
        const sortedCrawls = [...crawls].sort((a, b) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        setRecentCrawls(sortedCrawls.slice(0, 5));
        
        // Calculate stats
        const completed = crawls.filter(c => c.status === 'completed').length;
        const failed = crawls.filter(c => c.status === 'failed').length;
        const active = crawls.filter(c => c.status === 'running' || c.status === 'queued' || c.status === 'pending').length;
        
        // Get total pages from completed crawls
        let totalPages = 0;
        for (const crawl of crawls.filter(c => c.status === 'completed')) {
          try {
            const pages = await apiService.getCrawlPages(crawl.id, { limit: 1000 });
            totalPages += pages.length;
          } catch (e) {
            console.error('Error fetching pages for crawl:', crawl.id, e);
          }
        }
        
        setStats({
          totalCrawls: crawls.length,
          completedCrawls: completed,
          failedCrawls: failed,
          activeCrawls: active,
          totalPages,
        });
        
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg font-medium text-gray-500">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="container px-4 py-8 mx-auto max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-neutral-charcoal">Dashboard</h1>
        <p className="mt-2 text-neutral-steel">
          Welcome back, {user?.email}!
        </p>
      </div>

      {error && (
        <div className="p-4 mb-6 text-sm text-red-700 bg-red-100 rounded-md" role="alert">
          {error}
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg border border-primary-100 p-6 shadow-soft">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-neutral-steel">Total Crawls</p>
              <p className="text-3xl font-bold text-neutral-charcoal mt-2">{stats.totalCrawls}</p>
            </div>
            <div className="p-3 bg-secondary-100 rounded-lg">
              <Globe className="w-6 h-6 text-secondary-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-primary-100 p-6 shadow-soft">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-neutral-steel">Completed</p>
              <p className="text-3xl font-bold text-green-600 mt-2">{stats.completedCrawls}</p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-primary-100 p-6 shadow-soft">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-neutral-steel">Active</p>
              <p className="text-3xl font-bold text-blue-600 mt-2">{stats.activeCrawls}</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <Clock className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-primary-100 p-6 shadow-soft">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-neutral-steel">Pages Crawled</p>
              <p className="text-3xl font-bold text-secondary-600 mt-2">{stats.totalPages}</p>
            </div>
            <div className="p-3 bg-secondary-100 rounded-lg">
              <TrendingUp className="w-6 h-6 text-secondary-600" />
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Crawls - Takes 2 columns */}
        <div className="lg:col-span-2">
          <div className="p-6 bg-white rounded-lg border border-primary-100 shadow-soft">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-secondary-600" />
                <h2 className="text-xl font-semibold text-neutral-charcoal">Recent Crawls</h2>
              </div>
              <Link to="/crawls" className="text-sm font-medium text-secondary-600 hover:text-secondary-700">
                View all →
              </Link>
            </div>
            
            {recentCrawls.length > 0 ? (
              <div className="space-y-3">
                {recentCrawls.map((crawl) => (
                  <Link
                    key={crawl.id}
                    to={`/crawls/${crawl.id}`}
                    className="block p-4 rounded-lg border border-gray-200 hover:border-secondary-300 hover:bg-gray-50 transition-all"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-semibold text-neutral-charcoal truncate">
                          {crawl.name}
                        </h3>
                        <p className="text-xs text-neutral-steel mt-1 truncate">
                          {crawl.url}
                        </p>
                        <p className="text-xs text-neutral-steel/70 mt-1">
                          {new Date(crawl.created_at).toLocaleDateString()} at {new Date(crawl.created_at).toLocaleTimeString()}
                        </p>
                      </div>
                      <span className={`ml-4 inline-flex px-2.5 py-1 text-xs font-semibold rounded-full whitespace-nowrap ${getStatusBadgeClass(crawl.status)}`}>
                        {crawl.status}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <Globe className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-sm text-neutral-steel mb-4">No crawls yet</p>
                <button
                  onClick={() => navigate('/crawls?new=true')}
                  className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-secondary-500 hover:bg-secondary-hover rounded-lg transition-colors"
                >
                  Start Your First Crawl
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions - Takes 1 column */}
        <div>
          <div className="p-6 bg-white rounded-lg border border-primary-100 shadow-soft">
            <h2 className="text-xl font-semibold text-neutral-charcoal mb-6">Quick Actions</h2>
            <div className="space-y-3">
              <button
                onClick={() => navigate('/crawls?new=true')}
                className="w-full flex items-center p-4 bg-secondary-50 hover:bg-secondary-100 border border-secondary-200 rounded-lg transition-colors text-left"
              >
                <div className="p-2 mr-3 text-white bg-secondary-500 rounded-lg">
                  <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-neutral-charcoal">New Crawl</h3>
                  <p className="text-xs text-neutral-steel">Start a new website crawl</p>
                </div>
              </button>
              
              <Link 
                to="/crawls"
                className="w-full flex items-center p-4 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg transition-colors"
              >
                <div className="p-2 mr-3 text-white bg-gray-500 rounded-lg">
                  <Globe className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-neutral-charcoal">All Crawls</h3>
                  <p className="text-xs text-neutral-steel">View all your crawls</p>
                </div>
              </Link>
              
              <Link 
                to="/profile" 
                className="w-full flex items-center p-4 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg transition-colors"
              >
                <div className="p-2 mr-3 text-white bg-purple-500 rounded-lg">
                  <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-neutral-charcoal">Profile</h3>
                  <p className="text-xs text-neutral-steel">Manage your account</p>
                </div>
              </Link>
            </div>
          </div>

          {/* Quick Stats */}
          {stats.failedCrawls > 0 && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start gap-3">
                <XCircle className="w-5 h-5 text-red-600 mt-0.5" />
                <div>
                  <h3 className="text-sm font-semibold text-red-900">Failed Crawls</h3>
                  <p className="text-xs text-red-700 mt-1">
                    You have {stats.failedCrawls} failed crawl{stats.failedCrawls > 1 ? 's' : ''}.
                  </p>
                  <Link to="/crawls" className="text-xs font-medium text-red-600 hover:text-red-700 mt-2 inline-block">
                    Review →
                  </Link>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

    </div>
  );
};

export default DashboardPage;
