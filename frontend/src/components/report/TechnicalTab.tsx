import React from 'react';
import { AlertCircle, CheckCircle } from 'lucide-react';
import { CrawlReport } from '../../services/api';

interface TechnicalTabProps {
  report: CrawlReport;
}

const TechnicalTab: React.FC<TechnicalTabProps> = ({ report }) => {
  const r = report.report;
  if (!r) return null;

  return (
    <div className="space-y-6">
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
