import React, { useState } from 'react';
import { Loader2, FileBarChart, RefreshCw } from 'lucide-react';
import { CrawlReport } from '../../services/api';
import ExecutiveTab from './ExecutiveTab';
import PageAuditTab from './PageAuditTab';
import ContentBrandTab from './ContentBrandTab';
import TechnicalTab from './TechnicalTab';

interface ReportPanelProps {
  report: CrawlReport | null;
  reportLoading: boolean;
  generatingReport: boolean;
  onGenerateReport: () => void;
  crawlStatus?: string;
}

type ReportSubTab = 'executive' | 'page-audit' | 'content-brand' | 'technical';

const subTabs: { id: ReportSubTab; label: string }[] = [
  { id: 'executive', label: 'Executive' },
  { id: 'page-audit', label: 'Page Audit' },
  { id: 'content-brand', label: 'Content & Brand' },
  { id: 'technical', label: 'Technical' },
];

const ReportPanel: React.FC<ReportPanelProps> = ({
  report,
  reportLoading,
  generatingReport,
  onGenerateReport,
  crawlStatus,
}) => {
  const [activeSubTab, setActiveSubTab] = useState<ReportSubTab>('executive');

  // Loading state
  if (reportLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-6 h-6 animate-spin text-secondary-500 mr-3" />
        <span className="text-gray-500">Loading report...</span>
      </div>
    );
  }

  // Generating state
  if (generatingReport) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-secondary-500 mb-4" />
        <div className="text-lg font-medium text-gray-900 mb-2">Generating AI Report...</div>
        <p className="text-sm text-gray-500 max-w-md text-center">
          Analyzing pages, computing SEO scores, and synthesizing insights. This may take 30-60 seconds.
        </p>
      </div>
    );
  }

  // No report yet
  if (!report || !report.report) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <FileBarChart className="w-12 h-12 text-gray-300 mb-4" />
        <div className="text-lg font-medium text-gray-900 mb-2">No Report Generated</div>
        <p className="text-sm text-gray-500 mb-6 max-w-md text-center">
          {crawlStatus === 'completed'
            ? 'Generate an AI-powered analysis of this crawl with health scores, SEO audit, and strategic recommendations.'
            : 'Complete the crawl first, then generate an AI-powered report.'}
        </p>
        {crawlStatus === 'completed' && (
          <button
            onClick={onGenerateReport}
            className="px-6 py-2.5 bg-secondary-500 text-white rounded-lg font-medium hover:bg-secondary-600 transition-colors"
          >
            Generate Report
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header: Sub-tab navigation + Regenerate button */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-2 flex-wrap">
          {subTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveSubTab(tab.id)}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                activeSubTab === tab.id
                  ? 'bg-secondary-100 text-secondary-700 font-semibold'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <button
          onClick={onGenerateReport}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Regenerate
        </button>
      </div>

      {/* Active sub-tab content */}
      {activeSubTab === 'executive' && <ExecutiveTab report={report} />}
      {activeSubTab === 'page-audit' && <PageAuditTab report={report} />}
      {activeSubTab === 'content-brand' && <ContentBrandTab report={report} />}
      {activeSubTab === 'technical' && <TechnicalTab report={report} />}

      {/* Report metadata footer */}
      {report.generated_at && (
        <div className="text-center text-xs text-gray-400 pt-4 border-t border-gray-100">
          Report generated on {new Date(report.generated_at).toLocaleString()}
          {report.report?.usage && (
            <span className="ml-4">
              Cost: ${report.report.usage.total_cost_usd?.toFixed(4) || '0.0000'}
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default ReportPanel;
