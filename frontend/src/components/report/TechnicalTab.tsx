import React, { useState } from 'react';
import { AlertCircle, CheckCircle, Link2, AlertTriangle, ArrowDown, ArrowUp, Type, Network, ChevronDown, ChevronRight, ArrowRight, Code2 } from 'lucide-react';
import { CrawlReport } from '../../services/api';

interface TechnicalTabProps {
  report: CrawlReport;
}

const TechnicalTab: React.FC<TechnicalTabProps> = ({ report }) => {
  const [showAllPages, setShowAllPages] = useState(false);
  const [expandedClusters, setExpandedClusters] = useState<Set<string>>(new Set());

  const r = report.report;
  if (!r) return null;

  const il = r.internal_linking;
  const at = il?.anchor_text;
  const clusters = il?.topic_clusters;

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

  const clusterColor = (ratio: number) => {
    if (ratio >= 80) return 'bg-green-500';
    if (ratio >= 40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const clusterBadgeColor = (ratio: number) => {
    if (ratio >= 80) return 'text-green-700 bg-green-100';
    if (ratio >= 40) return 'text-yellow-700 bg-yellow-100';
    return 'text-red-700 bg-red-100';
  };

  const toggleCluster = (name: string) => {
    setExpandedClusters(prev => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  };

  const stripDomain = (url: string) => url.replace(/^https?:\/\/[^/]+/, '') || '/';

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
                        {stripDomain(page.url)}
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

          {/* Anchor Text Quality */}
          {at && (
            <div className={`rounded-lg border p-6 ${scoreBorderColor(at.anchor_score)}`}>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                    <Type className="w-5 h-5" />
                    Anchor Text Quality
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    How descriptive are your internal link anchor texts?
                  </p>
                </div>
                <div className="text-right">
                  <div className={`text-4xl font-bold ${scoreColor(at.anchor_score)}`}>
                    {at.anchor_score}
                  </div>
                  <div className="text-xs text-gray-500">out of 100</div>
                </div>
              </div>

              {/* Distribution Bar */}
              {(() => {
                const total = at.descriptive_count + at.partial_count + at.generic_count + at.missing_count;
                if (total === 0) return null;
                const pct = (n: number) => Math.max(n > 0 ? 2 : 0, Math.round(n / total * 100));
                return (
                  <div className="mb-4">
                    <div className="flex rounded-full overflow-hidden h-4 bg-gray-200">
                      {at.descriptive_count > 0 && (
                        <div className="bg-green-500 transition-all" style={{ width: `${pct(at.descriptive_count)}%` }} title={`Descriptive: ${at.descriptive_count}`} />
                      )}
                      {at.partial_count > 0 && (
                        <div className="bg-blue-400 transition-all" style={{ width: `${pct(at.partial_count)}%` }} title={`Partial: ${at.partial_count}`} />
                      )}
                      {at.generic_count > 0 && (
                        <div className="bg-yellow-500 transition-all" style={{ width: `${pct(at.generic_count)}%` }} title={`Generic: ${at.generic_count}`} />
                      )}
                      {at.missing_count > 0 && (
                        <div className="bg-red-500 transition-all" style={{ width: `${pct(at.missing_count)}%` }} title={`Missing: ${at.missing_count}`} />
                      )}
                    </div>
                    <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs text-gray-600">
                      <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-green-500 inline-block" /> Descriptive ({at.descriptive_count})</span>
                      <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-blue-400 inline-block" /> Partial ({at.partial_count})</span>
                      <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-yellow-500 inline-block" /> Generic ({at.generic_count})</span>
                      <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block" /> Missing ({at.missing_count})</span>
                    </div>
                  </div>
                );
              })()}

              {/* Worst Anchors Table */}
              {at.worst_anchors && at.worst_anchors.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Anchors Needing Improvement</h4>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-200">
                          <th className="text-left py-2 pr-3 text-gray-500 font-medium">Anchor Text</th>
                          <th className="text-left py-2 pr-3 text-gray-500 font-medium">Source Page</th>
                          <th className="text-left py-2 text-gray-500 font-medium">Target Page</th>
                        </tr>
                      </thead>
                      <tbody>
                        {at.worst_anchors.map((wa, i) => (
                          <tr key={i} className="border-b border-gray-50">
                            <td className="py-2 pr-3">
                              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                                wa.category === 'missing' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
                              }`}>
                                {wa.anchor}
                              </span>
                            </td>
                            <td className="py-2 pr-3 text-secondary-600 truncate max-w-[200px]">
                              <a href={wa.source_url} target="_blank" rel="noopener noreferrer" className="hover:underline">
                                {stripDomain(wa.source_url)}
                              </a>
                            </td>
                            <td className="py-2 text-secondary-600 truncate max-w-[200px]">
                              <a href={wa.target_url} target="_blank" rel="noopener noreferrer" className="hover:underline">
                                {stripDomain(wa.target_url)}
                              </a>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Topic Clusters */}
          {clusters && clusters.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-1 flex items-center gap-2">
                <Network className="w-5 h-5" />
                Topic Clusters
              </h3>
              <p className="text-sm text-gray-500 mb-4">
                Pages grouped by URL path. Low cross-linking means missed opportunities for related pages to reference each other.
              </p>
              <div className="space-y-3">
                {clusters.map((cluster) => {
                  const isExpanded = expandedClusters.has(cluster.cluster_name);
                  return (
                    <div key={cluster.cluster_name} className="border border-gray-100 rounded-lg overflow-hidden">
                      <button
                        onClick={() => toggleCluster(cluster.cluster_name)}
                        className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors text-left"
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          {isExpanded ? <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0" /> : <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0" />}
                          <div className="min-w-0">
                            <span className="font-medium text-gray-900">{cluster.cluster_name}</span>
                            <span className="text-xs text-gray-400 ml-2">{cluster.page_count} pages</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-3 flex-shrink-0">
                          <div className="w-24 h-2 rounded-full bg-gray-200 overflow-hidden">
                            <div className={`h-full rounded-full ${clusterColor(cluster.cross_link_ratio)}`} style={{ width: `${cluster.cross_link_ratio}%` }} />
                          </div>
                          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${clusterBadgeColor(cluster.cross_link_ratio)}`}>
                            {cluster.cross_link_ratio}%
                          </span>
                        </div>
                      </button>

                      {isExpanded && (
                        <div className="px-4 pb-4 border-t border-gray-100">
                          <div className="mt-3 text-xs text-gray-500 mb-2">
                            {cluster.cross_links_found} of {cluster.cross_links_possible} possible cross-links exist
                          </div>

                          {/* Pages in cluster */}
                          <div className="mb-3">
                            <div className="text-xs font-medium text-gray-500 mb-1">Pages</div>
                            <div className="flex flex-wrap gap-1">
                              {cluster.pages.map((p, i) => (
                                <a
                                  key={i}
                                  href={p.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-block text-xs px-2 py-1 bg-gray-100 text-secondary-600 rounded hover:bg-gray-200 truncate max-w-[250px]"
                                >
                                  {stripDomain(p.url)}
                                </a>
                              ))}
                            </div>
                          </div>

                          {/* Missing links suggestions */}
                          {cluster.missing_links && cluster.missing_links.length > 0 && (
                            <div>
                              <div className="text-xs font-medium text-gray-500 mb-2">Suggested Cross-Links</div>
                              <div className="space-y-1.5">
                                {cluster.missing_links.map((ml, i) => (
                                  <div key={i} className="flex items-center gap-2 text-xs bg-yellow-50 border border-yellow-100 rounded px-3 py-2">
                                    <span className="text-gray-700 truncate max-w-[180px]" title={ml.from_title}>
                                      {stripDomain(ml.from_url)}
                                    </span>
                                    <ArrowRight className="w-3 h-3 text-gray-400 flex-shrink-0" />
                                    <span className="text-gray-700 truncate max-w-[180px]" title={ml.to_title}>
                                      {stripDomain(ml.to_url)}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Schema / Structured Data Coverage */}
          {r.schema_coverage && (
            <div className={`rounded-lg border p-6 ${scoreBorderColor(r.schema_coverage.schema_score)}`}>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                    <Code2 className="w-5 h-5" />
                    Schema / Structured Data
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {r.schema_coverage.pages_with_schema} of {r.metrics?.total_pages || '?'} pages have structured data
                    ({r.schema_coverage.schema_coverage_pct}% coverage)
                  </p>
                </div>
                <div className="text-right">
                  <div className={`text-4xl font-bold ${scoreColor(r.schema_coverage.schema_score)}`}>
                    {r.schema_coverage.schema_score}
                  </div>
                  <div className="text-xs text-gray-500">out of 100</div>
                </div>
              </div>

              {/* Types Found */}
              {r.schema_coverage.types_found.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Schema Types Detected</h4>
                  <div className="flex flex-wrap gap-2">
                    {r.schema_coverage.types_found.map((type) => (
                      <span key={type} className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-green-100 text-green-800 border border-green-200">
                        {type}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Missing Recommended */}
              {r.schema_coverage.missing_recommended.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Recommended But Missing</h4>
                  <div className="flex flex-wrap gap-2">
                    {r.schema_coverage.missing_recommended.map((type) => (
                      <span key={type} className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-200">
                        {type}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Pages Without Schema */}
              {r.schema_coverage.pages_without_schema.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Pages Without Structured Data</h4>
                  <div className="space-y-1.5">
                    {r.schema_coverage.pages_without_schema.map((page, i) => (
                      <div key={i} className="flex items-center py-1.5 px-3 bg-white/70 rounded border border-gray-100 text-sm">
                        <a href={page.url} target="_blank" rel="noopener noreferrer" className="text-secondary-600 hover:underline truncate">
                          {stripDomain(page.url)}
                        </a>
                        {page.title && page.title !== 'Untitled' && (
                          <span className="text-xs text-gray-400 ml-2 truncate">{page.title}</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
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
                            {stripDomain(page.url)}
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
                        {stripDomain(url)}
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
