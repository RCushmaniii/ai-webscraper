import React, { useState } from 'react';
import { AlertCircle, CheckCircle, Link2, AlertTriangle, ArrowDown, ArrowUp } from 'lucide-react';
import { CrawlReport } from '../../services/api';

interface TechnicalTabProps {
  report: CrawlReport;
}

const TechnicalTab: React.FC<TechnicalTabProps> = ({ report }) => {
  const r = report.report;
  if (!r) return null;

  const il = r.internal_linking;
  const [showAllPages, setShowAllPages] = useState(false);

  const scoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const scoreBorderColor = (score: number) => {
    if (score >= 80) return 'border-green-200 bg-green-50';
    if (score >= 60) return 'border-yellow-200 bg-yellow-50';
    return 'border-red-200 bg-red-50';
  };

  return (
    <div className="space-y-6">
      {/* Internal Linking Analysis */}
      {il && (
        <>
          {/* Linking Health Score */}
          <div className={`rounded-lg border p-6 ${scoreBorderColor(il.linking_score)}`}>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <Link2 className="w-5 h-5" />
                  Internal Linking Health
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  {il.total_internal_links} internal links across {il.page_details?.length || 0} pages
                  {il.orphan_count > 0 && ` · ${il.orphan_count} orphan page${il.orphan_count > 1 ? 's' : ''}`}
                  {il.dead_end_count > 0 && ` · ${il.dead_end_count} dead end${il.dead_end_count > 1 ? 's' : ''}`}
                </p>
              </div>
              <div className="text-right">
                <div className={`text-4xl font-bold ${scoreColor(il.linking_score)}`}>
                  {il.linking_score}
                </div>
                <div className="text-xs text-gray-500">out of 100</div>
              </div>
            </div>
          </div>

          {/* Depth Distribution */}
          {il.depth_distribution && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Click Depth Distribution</h3>
              <p className="text-sm text-gray-500 mb-4">How many clicks from the homepage to reach each page</p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                {Object.entries(il.depth_distribution)
                  .sort(([a], [b]) => {
                    if (a === '3+') return 1;
                    if (b === '3+') return -1;
                    return Number(a) - Number(b);
                  })
                  .map(([depth, count]) => (
                    <div key={depth} className="text-center p-3 rounded-lg bg-gray-50 border border-gray-100">
                      <div className="text-2xl font-bold text-gray-900">{count}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {depth === '0' ? 'Homepage' : depth === '3+' ? '3+ clicks' : `${depth} click${depth === '1' ? '' : 's'}`}
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Orphan Pages Warning */}
          {il.orphan_pages && il.orphan_pages.length > 0 && (
            <div className="bg-white rounded-lg border border-red-200 p-6">
              <h3 className="text-lg font-semibold text-red-800 mb-2 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5" />
                Orphan Pages ({il.orphan_pages.length})
              </h3>
              <p className="text-sm text-gray-600 mb-4">
                These pages have no internal links pointing to them. Search engines and users can only reach them via direct URL or external links.
              </p>
              <div className="space-y-2">
                {il.orphan_pages.map((page, i) => (
                  <div key={i} className="flex items-center justify-between py-2 px-3 bg-red-50 rounded border border-red-100">
                    <div>
                      <a
                        href={page.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-secondary-600 hover:underline font-medium"
                      >
                        {page.url.replace(/^https?:\/\/[^/]+/, '') || '/'}
                      </a>
                      {page.title && page.title !== 'Untitled' && (
                        <span className="text-xs text-gray-500 ml-2">{page.title}</span>
                      )}
                    </div>
                    <span className="text-xs text-gray-400">Depth {page.depth}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Link Distribution Table */}
          {il.page_details && il.page_details.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Page Link Distribution</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-2 pr-4 text-gray-600 font-medium">Page</th>
                      <th className="text-center py-2 px-3 text-gray-600 font-medium whitespace-nowrap">
                        <span className="flex items-center justify-center gap-1">
                          <ArrowDown className="w-3 h-3" /> Inbound
                        </span>
                      </th>
                      <th className="text-center py-2 px-3 text-gray-600 font-medium whitespace-nowrap">
                        <span className="flex items-center justify-center gap-1">
                          <ArrowUp className="w-3 h-3" /> Outbound
                        </span>
                      </th>
                      <th className="text-center py-2 px-3 text-gray-600 font-medium">Depth</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(showAllPages ? il.page_details : il.page_details.slice(0, 10)).map((page, i) => (
                      <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="py-2 pr-4">
                          <a
                            href={page.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-secondary-600 hover:underline truncate block max-w-xs"
                          >
                            {page.url.replace(/^https?:\/\/[^/]+/, '') || '/'}
                          </a>
                          {page.title && page.title !== 'Untitled' && (
                            <div className="text-xs text-gray-400 truncate max-w-xs">{page.title}</div>
                          )}
                        </td>
                        <td className="text-center py-2 px-3">
                          <span className={`font-medium ${page.inbound === 0 ? 'text-red-600' : 'text-gray-900'}`}>
                            {page.inbound}
                          </span>
                        </td>
                        <td className="text-center py-2 px-3">
                          <span className={`font-medium ${page.outbound === 0 ? 'text-yellow-600' : 'text-gray-900'}`}>
                            {page.outbound}
                          </span>
                        </td>
                        <td className="text-center py-2 px-3 text-gray-600">{page.depth}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {il.page_details.length > 10 && (
                <button
                  onClick={() => setShowAllPages(!showAllPages)}
                  className="mt-3 text-sm text-secondary-600 hover:underline"
                >
                  {showAllPages ? 'Show less' : `Show all ${il.page_details.length} pages`}
                </button>
              )}
            </div>
          )}
        </>
      )}

      {/* Critical Issues */}
      {r.executive_summary?.critical_issues && r.executive_summary.critical_issues.length > 0 && (
        <div className="bg-white rounded-lg border border-red-200 p-6">
          <h3 className="text-lg font-semibold text-red-800 mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            Critical Issues
          </h3>
          <div className="space-y-4">
            {r.executive_summary.critical_issues.map((issue, index) => (
              <div key={index} className="border-l-4 border-red-500 pl-4 py-2">
                <div className="font-medium text-gray-900">{issue.title}</div>
                <div className="text-sm text-gray-600 mt-1">{issue.description}</div>
                {issue.affected_urls && issue.affected_urls.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {issue.affected_urls.map((url: string, i: number) => (
                      <a
                        key={i}
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block text-xs text-secondary-600 hover:underline truncate"
                      >
                        {url.replace(/^https?:\/\/[^/]+/, '') || '/'}
                      </a>
                    ))}
                  </div>
                )}
                <div className="text-sm text-gray-500 mt-1">
                  <span className="font-medium">Affects:</span> {issue.pages_affected} {issue.pages_affected === 1 ? 'page' : 'pages'}
                </div>
                <div className="text-sm text-secondary-600 mt-1">
                  <span className="font-medium">Action:</span> {issue.recommended_action}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Wins */}
      {r.executive_summary?.quick_wins && r.executive_summary.quick_wins.length > 0 && (
        <div className="bg-white rounded-lg border border-green-200 p-6">
          <h3 className="text-lg font-semibold text-green-800 mb-4 flex items-center gap-2">
            <CheckCircle className="w-5 h-5" />
            Quick Wins
          </h3>
          <ul className="space-y-2">
            {r.executive_summary.quick_wins.map((win, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="text-green-500 mt-0.5">&bull;</span>
                <span className="text-gray-700">{win}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Strategic Recommendations */}
      {r.executive_summary?.strategic_recommendations && r.executive_summary.strategic_recommendations.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Strategic Recommendations</h3>
          <div className="space-y-4">
            {r.executive_summary.strategic_recommendations.map((rec, index) => (
              <div key={index} className="border border-gray-100 rounded-lg p-4 bg-gray-50">
                <div className="font-medium text-gray-900">{rec.title}</div>
                <div className="text-sm text-gray-600 mt-1">{rec.description}</div>
                <div className="flex flex-wrap gap-4 mt-2 text-xs text-gray-500">
                  <span><strong>Impact:</strong> {rec.expected_impact}</span>
                  <span><strong>Effort:</strong> {rec.effort_estimate}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TechnicalTab;
