import React from 'react';
import { CrawlReport } from '../../services/api';

interface ExecutiveTabProps {
  report: CrawlReport;
}

const scoreColor = (score: number) =>
  score >= 80 ? 'text-green-600' : score >= 60 ? 'text-yellow-600' : 'text-red-600';

const rateColor = (rate: number) =>
  rate >= 80 ? 'text-green-600' : rate >= 50 ? 'text-yellow-600' : 'text-red-600';

const ExecutiveTab: React.FC<ExecutiveTabProps> = ({ report }) => {
  const r = report.report;
  if (!r) return null;

  return (
    <div className="space-y-6">
      {/* Health Score Overview */}
      <div className="bg-gradient-to-r from-secondary-50 to-blue-50 rounded-xl p-6 border border-secondary-100">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-1">Site Health Score</h3>
            <p className="text-gray-600">{r.executive_summary?.one_line_summary}</p>
          </div>
          <div className="text-right">
            <div className={`text-5xl font-bold ${scoreColor(r.executive_summary?.site_health_score || 0)}`}>
              {r.executive_summary?.site_health_score || 0}
            </div>
            <div className="text-sm text-gray-500">out of 100</div>
          </div>
        </div>
      </div>

      {/* Score Breakdown */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Technical SEO', score: r.executive_summary?.technical_seo_score },
          { label: 'Content Quality', score: r.executive_summary?.content_quality_score },
          { label: 'User Experience', score: r.executive_summary?.user_experience_score },
          { label: 'Trust Signals', score: r.executive_summary?.trust_signals_score },
        ].map((item) => (
          <div key={item.label} className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="text-sm text-gray-600 mb-1">{item.label}</div>
            <div className={`text-2xl font-bold ${scoreColor(item.score || 0)}`}>
              {item.score || 0}
            </div>
          </div>
        ))}
      </div>

      {/* Crawl Metrics */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Crawl Metrics</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{r.metrics?.total_pages || 0}</div>
            <div className="text-sm text-gray-500">Pages Crawled</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{r.metrics?.total_issues || 0}</div>
            <div className="text-sm text-gray-500">Total Issues</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">{r.metrics?.broken_links || 0}</div>
            <div className="text-sm text-gray-500">Broken Links</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">{r.metrics?.missing_meta || 0}</div>
            <div className="text-sm text-gray-500">Missing Meta</div>
          </div>
        </div>
      </div>

      {/* SEO Pass Rates */}
      {r.summary_stats && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">SEO Pass Rates</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {[
              { label: 'Title Tags', rate: r.summary_stats.title_pass_rate, target: '30-60 chars' },
              { label: 'Meta Descriptions', rate: r.summary_stats.meta_pass_rate, target: '120-160 chars' },
              { label: 'H1 Tags', rate: r.summary_stats.h1_pass_rate, target: 'Present' },
              { label: 'Content Depth', rate: r.summary_stats.content_pass_rate, target: '300+ words' },
              { label: 'Response Time', rate: r.summary_stats.performance_pass_rate, target: '<1000ms' },
            ].map((item) => (
              <div key={item.label} className="text-center">
                <div className={`text-2xl font-bold ${rateColor(item.rate)}`}>
                  {item.rate}%
                </div>
                <div className="text-sm font-medium text-gray-700">{item.label}</div>
                <div className="text-xs text-gray-400">{item.target}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Plan */}
      {r.executive_summary?.action_plan_summary && (
        <div className="bg-secondary-50 rounded-lg border border-secondary-200 p-6">
          <h3 className="text-lg font-semibold text-secondary-900 mb-3">Recommended Action Plan</h3>
          <p className="text-gray-700">{r.executive_summary.action_plan_summary}</p>
        </div>
      )}

      {/* Strengths & Weaknesses */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg border border-green-200 p-6">
          <h3 className="text-lg font-semibold text-green-800 mb-3">Strengths</h3>
          <p className="text-gray-700">{r.executive_summary?.strengths_summary || 'No strengths summary available.'}</p>
        </div>
        <div className="bg-white rounded-lg border border-orange-200 p-6">
          <h3 className="text-lg font-semibold text-orange-800 mb-3">Areas for Improvement</h3>
          <p className="text-gray-700">{r.executive_summary?.weaknesses_summary || 'No weaknesses summary available.'}</p>
        </div>
      </div>
    </div>
  );
};

export default ExecutiveTab;
