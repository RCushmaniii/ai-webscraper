import React, { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';
import { CrawlReport } from '../../services/api';

interface PageAuditTabProps {
  report: CrawlReport;
}

type SortField = 'url' | 'score' | 'issue_count';

const ITEMS_PER_PAGE = 25;

const PageAuditTab: React.FC<PageAuditTabProps> = ({ report }) => {
  const r = report.report;

  const [sortField, setSortField] = useState<SortField>('score');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [findingSeverityFilter, setFindingSeverityFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all');

  const sortedAudits = useMemo(() => {
    if (!r?.page_audits) return [];
    return [...r.page_audits].sort((a, b) => {
      const dir = sortDir === 'asc' ? 1 : -1;
      if (sortField === 'url') return a.url.localeCompare(b.url) * dir;
      if (sortField === 'score') return (a.score - b.score) * dir;
      return (a.issue_count - b.issue_count) * dir;
    });
  }, [r?.page_audits, sortField, sortDir]);

  const filteredFindings = useMemo(() => {
    if (!r?.data_findings) return [];
    if (findingSeverityFilter === 'all') return r.data_findings;
    return r.data_findings.filter(f => f.severity === findingSeverityFilter);
  }, [r?.data_findings, findingSeverityFilter]);

  if (!r) return null;

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDir(field === 'url' ? 'asc' : 'asc');
    }
    setCurrentPage(1);
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return <ChevronDown className="w-3 h-3 text-gray-300" />;
    return sortDir === 'asc'
      ? <ChevronUp className="w-3 h-3 text-secondary-600" />
      : <ChevronDown className="w-3 h-3 text-secondary-600" />;
  };

  const totalPages = Math.ceil(sortedAudits.length / ITEMS_PER_PAGE);
  const paginatedAudits = sortedAudits.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  const statusIcon = (status: string) => {
    if (status === 'pass') return <span className="text-green-600">&#10003;</span>;
    if (status === 'missing' || status === 'empty') return <span className="text-red-600">&#10007;</span>;
    return <span className="text-yellow-600">&#9888;</span>;
  };

  return (
    <div className="space-y-6">
      {/* Data-Driven Findings */}
      {r.data_findings && r.data_findings.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-1">Specific Findings</h3>
              <p className="text-sm text-gray-500">{filteredFindings.length} issues found by automated analysis</p>
            </div>
            <select
              value={findingSeverityFilter}
              onChange={(e) => setFindingSeverityFilter(e.target.value as any)}
              className="text-sm border border-gray-300 rounded-md px-3 py-1.5 text-gray-700 focus:outline-none focus:ring-2 focus:ring-secondary-500"
            >
              <option value="all">All severities</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-3 font-medium text-gray-600">Severity</th>
                  <th className="text-left py-2 px-3 font-medium text-gray-600">Category</th>
                  <th className="text-left py-2 px-3 font-medium text-gray-600">Finding</th>
                  <th className="text-left py-2 px-3 font-medium text-gray-600">Current</th>
                  <th className="text-left py-2 px-3 font-medium text-gray-600">Target</th>
                </tr>
              </thead>
              <tbody>
                {filteredFindings.slice(0, 50).map((finding: any, i: number) => (
                  <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-2 px-3">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        finding.severity === 'high' ? 'bg-red-100 text-red-700' :
                        finding.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-blue-100 text-blue-700'
                      }`}>
                        {finding.severity}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-gray-600">{finding.category}</td>
                    <td className="py-2 px-3 text-gray-900">{finding.finding}</td>
                    <td className="py-2 px-3 text-gray-600 max-w-[200px] truncate" title={String(finding.current_value || '')}>
                      {finding.current_value != null ? (
                        typeof finding.current_value === 'string' ? `"${finding.current_value.substring(0, 40)}${finding.current_value.length > 40 ? '...' : ''}"` : String(finding.current_value)
                      ) : '\u2014'}
                      {finding.current_length ? ` (${finding.current_length} chars)` : ''}
                    </td>
                    <td className="py-2 px-3 text-gray-500">{finding.target || '\u2014'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Per-Page Audit Table */}
      {r.page_audits && r.page_audits.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">Page-by-Page Audit</h3>
          <p className="text-sm text-gray-500 mb-4">Every page graded on SEO fundamentals</p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-3 font-medium text-gray-600 cursor-pointer select-none" onClick={() => handleSort('url')}>
                    <span className="inline-flex items-center gap-1">Page <SortIcon field="url" /></span>
                  </th>
                  <th className="text-center py-2 px-3 font-medium text-gray-600 cursor-pointer select-none" onClick={() => handleSort('score')}>
                    <span className="inline-flex items-center gap-1">Score <SortIcon field="score" /></span>
                  </th>
                  <th className="text-center py-2 px-3 font-medium text-gray-600">Title</th>
                  <th className="text-center py-2 px-3 font-medium text-gray-600">Meta</th>
                  <th className="text-center py-2 px-3 font-medium text-gray-600">H1</th>
                  <th className="text-center py-2 px-3 font-medium text-gray-600">Content</th>
                  <th className="text-center py-2 px-3 font-medium text-gray-600">Speed</th>
                  <th className="text-right py-2 px-3 font-medium text-gray-600 cursor-pointer select-none" onClick={() => handleSort('issue_count')}>
                    <span className="inline-flex items-center gap-1">Issues <SortIcon field="issue_count" /></span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {paginatedAudits.map((pa: any, i: number) => {
                  const urlPath = pa.url.replace(/^https?:\/\/[^/]+/, '') || '/';
                  return (
                    <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-2 px-3">
                        <a href={pa.url} target="_blank" rel="noopener noreferrer"
                          className="text-secondary-600 hover:underline truncate block max-w-[200px]" title={pa.url}>
                          {urlPath}
                        </a>
                      </td>
                      <td className="py-2 px-3 text-center">
                        <span className={`font-bold ${
                          pa.score >= 80 ? 'text-green-600' : pa.score >= 50 ? 'text-yellow-600' : 'text-red-600'
                        }`}>
                          {pa.score}
                        </span>
                      </td>
                      <td className="py-2 px-3 text-center">{statusIcon(pa.checks.title.status)}</td>
                      <td className="py-2 px-3 text-center">{statusIcon(pa.checks.meta_description.status)}</td>
                      <td className="py-2 px-3 text-center">{statusIcon(pa.checks.h1.status)}</td>
                      <td className="py-2 px-3 text-center">{statusIcon(pa.checks.content_depth.status)}</td>
                      <td className="py-2 px-3 text-center">{statusIcon(pa.checks.response_time.status)}</td>
                      <td className="py-2 px-3 text-right text-gray-600">{pa.issue_count}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
              <div className="text-sm text-gray-500">
                Showing {(currentPage - 1) * ITEMS_PER_PAGE + 1}-{Math.min(currentPage * ITEMS_PER_PAGE, sortedAudits.length)} of {sortedAudits.length} pages
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PageAuditTab;
