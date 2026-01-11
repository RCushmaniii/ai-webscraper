import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiService, Crawl } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import {
  Globe,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  Activity,
  AlertTriangle,
  BookOpen,
  Zap,
  Loader2,
  ArrowRight,
  BarChart3,
  Link2
} from 'lucide-react';

interface DashboardStats {
  totalCrawls: number;
  completedCrawls: number;
  failedCrawls: number;
  activeCrawls: number;
  totalPages: number;
  totalBrokenLinks: number;
  totalIssues: number;
}

const DashboardPage: React.FC = () => {
  const [recentCrawls, setRecentCrawls] = useState<Crawl[]>([]);
  const [stats, setStats] = useState<DashboardStats>({
    totalCrawls: 0,
    completedCrawls: 0,
    failedCrawls: 0,
    activeCrawls: 0,
    totalPages: 0,
    totalBrokenLinks: 0,
    totalIssues: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user, isAdmin } = useAuth();
  const navigate = useNavigate();

  // Usage limits (could come from user plan in future)
  const usageLimits = {
    pages: isAdmin ? 50000 : 5000,
    crawls: isAdmin ? 1000 : 100,
  };

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
        const active = crawls.filter(c => c.status === 'running' || c.status === 'queued' || c.status === 'pending' || c.status === 'in_progress').length;

        // Get total pages and issues from completed crawls
        let totalPages = 0;
        let totalBrokenLinks = 0;
        let totalIssues = 0;

        for (const crawl of crawls.filter(c => c.status === 'completed').slice(0, 10)) {
          try {
            const [pages, links, issues] = await Promise.all([
              apiService.getCrawlPages(crawl.id, { limit: 1000 }).catch(() => []),
              apiService.getCrawlLinks(crawl.id, { is_broken: true, limit: 100 }).catch(() => []),
              apiService.getCrawlIssues(crawl.id, { limit: 100 }).catch(() => [])
            ]);
            totalPages += pages.length;
            totalBrokenLinks += links.length;
            totalIssues += issues.length;
          } catch (e) {
            console.error('Error fetching data for crawl:', crawl.id, e);
          }
        }

        setStats({
          totalCrawls: crawls.length,
          completedCrawls: completed,
          failedCrawls: failed,
          activeCrawls: active,
          totalPages,
          totalBrokenLinks,
          totalIssues,
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

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
            <CheckCircle className="w-3 h-3" />
            Completed
          </span>
        );
      case 'running':
      case 'in_progress':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
            <Loader2 className="w-3 h-3 animate-spin" />
            Running
          </span>
        );
      case 'queued':
      case 'pending':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
            <Clock className="w-3 h-3" />
            Queued
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
            <XCircle className="w-3 h-3" />
            Failed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
            {status}
          </span>
        );
    }
  };

  // Calculate success rate
  const successRate = stats.totalCrawls > 0
    ? Math.round((stats.completedCrawls / stats.totalCrawls) * 100)
    : 0;

  // Calculate usage percentage
  const usagePercentage = Math.min((stats.totalPages / usageLimits.pages) * 100, 100);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3">
          <Loader2 className="w-6 h-6 text-secondary-500 animate-spin" />
          <span className="text-lg font-medium text-gray-500">Loading dashboard...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container px-4 py-8 mx-auto max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-neutral-charcoal">Dashboard</h1>
        <p className="mt-2 text-neutral-steel">
          Welcome back{user?.user_metadata?.full_name ? `, ${user.user_metadata.full_name}` : ''}!
        </p>
      </div>

      {error && (
        <div className="p-4 mb-6 text-sm text-red-700 bg-red-100 rounded-md" role="alert">
          {error}
        </div>
      )}

      {/* Stats Cards - Reordered with Active first when > 0 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Active Crawls - Prominent when > 0 */}
        <div className={`bg-white rounded-lg border p-6 shadow-soft transition-all ${
          stats.activeCrawls > 0
            ? 'border-blue-300 ring-2 ring-blue-100 animate-pulse-subtle'
            : 'border-primary-100'
        }`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-neutral-steel">Active</p>
              <p className={`text-3xl font-bold mt-2 ${
                stats.activeCrawls > 0 ? 'text-blue-600' : 'text-gray-400'
              }`}>
                {stats.activeCrawls}
              </p>
              {stats.activeCrawls > 0 && (
                <p className="text-xs text-blue-600 mt-1 flex items-center gap-1">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Crawling now
                </p>
              )}
            </div>
            <div className={`p-3 rounded-lg ${
              stats.activeCrawls > 0 ? 'bg-blue-100' : 'bg-gray-100'
            }`}>
              <Activity className={`w-6 h-6 ${
                stats.activeCrawls > 0 ? 'text-blue-600' : 'text-gray-400'
              }`} />
            </div>
          </div>
        </div>

        {/* Total Crawls */}
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

        {/* Success Rate (replaces redundant "Completed") */}
        <div className="bg-white rounded-lg border border-primary-100 p-6 shadow-soft">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-neutral-steel">Success Rate</p>
              <p className={`text-3xl font-bold mt-2 ${
                successRate >= 90 ? 'text-green-600' :
                successRate >= 70 ? 'text-yellow-600' :
                'text-red-600'
              }`}>
                {successRate}%
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {stats.completedCrawls}/{stats.totalCrawls} completed
              </p>
            </div>
            <div className={`p-3 rounded-lg ${
              successRate >= 90 ? 'bg-green-100' :
              successRate >= 70 ? 'bg-yellow-100' :
              'bg-red-100'
            }`}>
              <CheckCircle className={`w-6 h-6 ${
                successRate >= 90 ? 'text-green-600' :
                successRate >= 70 ? 'text-yellow-600' :
                'text-red-600'
              }`} />
            </div>
          </div>
        </div>

        {/* Pages Crawled */}
        <div className="bg-white rounded-lg border border-primary-100 p-6 shadow-soft">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-neutral-steel">Pages Crawled</p>
              <p className="text-3xl font-bold text-secondary-600 mt-2">{stats.totalPages.toLocaleString()}</p>
            </div>
            <div className="p-3 bg-secondary-100 rounded-lg">
              <TrendingUp className="w-6 h-6 text-secondary-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Crawls - Takes 2 columns */}
        <div className="lg:col-span-2 space-y-6">
          <div className="p-6 bg-white rounded-lg border border-primary-100 shadow-soft">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-secondary-600" />
                <h2 className="text-xl font-semibold text-neutral-charcoal">Recent Crawls</h2>
              </div>
              <Link to="/crawls" className="text-sm font-medium text-secondary-600 hover:text-secondary-700 flex items-center gap-1">
                View all
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            {recentCrawls.length > 0 ? (
              <div className="space-y-2">
                {recentCrawls.map((crawl) => (
                  <Link
                    key={crawl.id}
                    to={`/crawls/${crawl.id}`}
                    className="block p-4 rounded-lg border border-gray-200 hover:border-secondary-300 hover:bg-secondary-50/30 hover:shadow-sm transition-all group"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0 mr-4">
                        <h3 className="text-sm font-semibold text-neutral-charcoal truncate group-hover:text-secondary-700">
                          {crawl.name}
                        </h3>
                        <p className="text-xs text-neutral-steel mt-1 truncate">
                          {crawl.url}
                        </p>
                        <p className="text-xs text-neutral-steel/60 mt-1">
                          {new Date(crawl.created_at).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            hour: 'numeric',
                            minute: '2-digit'
                          })}
                        </p>
                      </div>
                      {getStatusBadge(crawl.status)}
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

          {/* Usage Progress Widget */}
          <div className="p-6 bg-white rounded-lg border border-primary-100 shadow-soft">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-secondary-600" />
                <h2 className="text-lg font-semibold text-neutral-charcoal">Usage This Month</h2>
              </div>
              <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded">
                {isAdmin ? 'Admin Plan' : 'Free Plan'}
              </span>
            </div>
            <div className="space-y-4">
              {/* Pages Usage */}
              <div>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-600">Pages Crawled</span>
                  <span className="font-medium text-gray-900">
                    {stats.totalPages.toLocaleString()} / {usageLimits.pages.toLocaleString()}
                  </span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      usagePercentage >= 90 ? 'bg-red-500' :
                      usagePercentage >= 70 ? 'bg-yellow-500' :
                      'bg-secondary-500'
                    }`}
                    style={{ width: `${usagePercentage}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {usagePercentage >= 90
                    ? 'Approaching limit - consider upgrading'
                    : `${(100 - usagePercentage).toFixed(0)}% remaining`}
                </p>
              </div>
              {/* Crawls Usage */}
              <div>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-600">Total Crawls</span>
                  <span className="font-medium text-gray-900">
                    {stats.totalCrawls} / {usageLimits.crawls.toLocaleString()}
                  </span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-secondary-500 rounded-full transition-all"
                    style={{ width: `${Math.min((stats.totalCrawls / usageLimits.crawls) * 100, 100)}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Quick Actions + Health */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <div className="p-6 bg-white rounded-lg border border-primary-100 shadow-soft">
            <h2 className="text-xl font-semibold text-neutral-charcoal mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <button
                onClick={() => navigate('/crawls?new=true')}
                className="w-full flex items-center p-4 bg-secondary-50 hover:bg-secondary-100 border border-secondary-200 rounded-lg transition-colors text-left group"
              >
                <div className="p-2 mr-3 text-white bg-secondary-500 rounded-lg group-hover:bg-secondary-600 transition-colors">
                  <Zap className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-neutral-charcoal">New Crawl</h3>
                  <p className="text-xs text-neutral-steel">Start a new website crawl</p>
                </div>
              </button>

              <Link
                to="/docs"
                className="w-full flex items-center p-4 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg transition-colors"
              >
                <div className="p-2 mr-3 text-white bg-indigo-500 rounded-lg">
                  <BookOpen className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-neutral-charcoal">Documentation</h3>
                  <p className="text-xs text-neutral-steel">Learn how to use the API</p>
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

          {/* Health Summary Widget */}
          <div className="p-6 bg-white rounded-lg border border-primary-100 shadow-soft">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-5 h-5 text-yellow-600" />
              <h2 className="text-lg font-semibold text-neutral-charcoal">Site Health</h2>
            </div>

            {(stats.totalBrokenLinks > 0 || stats.totalIssues > 0 || stats.failedCrawls > 0) ? (
              <div className="space-y-3">
                {stats.totalBrokenLinks > 0 && (
                  <div className="flex items-center justify-between p-3 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-center gap-2">
                      <Link2 className="w-4 h-4 text-red-600" />
                      <span className="text-sm text-red-800">Broken Links</span>
                    </div>
                    <span className="text-sm font-bold text-red-600">{stats.totalBrokenLinks}</span>
                  </div>
                )}

                {stats.totalIssues > 0 && (
                  <div className="flex items-center justify-between p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-yellow-600" />
                      <span className="text-sm text-yellow-800">SEO Issues</span>
                    </div>
                    <span className="text-sm font-bold text-yellow-600">{stats.totalIssues}</span>
                  </div>
                )}

                {stats.failedCrawls > 0 && (
                  <div className="flex items-center justify-between p-3 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-center gap-2">
                      <XCircle className="w-4 h-4 text-red-600" />
                      <span className="text-sm text-red-800">Failed Crawls</span>
                    </div>
                    <span className="text-sm font-bold text-red-600">{stats.failedCrawls}</span>
                  </div>
                )}

                <Link
                  to="/crawls"
                  className="block text-center text-sm font-medium text-secondary-600 hover:text-secondary-700 mt-2"
                >
                  Review Issues →
                </Link>
              </div>
            ) : (
              <div className="text-center py-4">
                <CheckCircle className="w-10 h-10 text-green-500 mx-auto mb-2" />
                <p className="text-sm text-green-700 font-medium">All systems healthy</p>
                <p className="text-xs text-gray-500 mt-1">No issues detected</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* CSS for subtle pulse animation */}
      <style>{`
        @keyframes pulse-subtle {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.85; }
        }
        .animate-pulse-subtle {
          animation: pulse-subtle 2s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
};

export default DashboardPage;
