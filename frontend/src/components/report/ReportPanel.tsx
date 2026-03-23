import React, { useState, useRef, useEffect } from 'react';
import { Loader2, FileBarChart, RefreshCw, Download, FileText, Table } from 'lucide-react';
import { toast } from 'sonner';
import { apiService, CrawlReport } from '../../services/api';
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
  crawlId?: string;
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
  crawlId,
}) => {
  const [activeSubTab, setActiveSubTab] = useState<ReportSubTab>('executive');
  const [exportOpen, setExportOpen] = useState(false);
  const [exporting, setExporting] = useState(false);
  const exportRef = useRef<HTMLDivElement>(null);

  // Close export dropdown on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (exportRef.current && !exportRef.current.contains(e.target as Node)) {
        setExportOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const triggerDownload = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleExportPdf = async () => {
    if (!crawlId) return;
    setExporting(true);
    setExportOpen(false);
    try {
      const blob = await apiService.exportReportPdf(crawlId);
      triggerDownload(blob, `cushlabs_report_${crawlId}.pdf`);
      toast.success('PDF downloaded');
    } catch (err: any) {
      toast.error('PDF export failed: ' + (err?.message || 'Unknown error'));
    } finally {
      setExporting(false);
    }
  };

  const handleExportCsv = async (type: 'page_audits' | 'findings') => {
    if (!crawlId) return;
    setExporting(true);
    setExportOpen(false);
    try {
      const blob = await apiService.exportReportCsv(crawlId, type);
      triggerDownload(blob, `cushlabs_${type}_${crawlId}.csv`);
      toast.success('CSV downloaded');
    } catch (err: any) {
      toast.error('CSV export failed: ' + (err?.message || 'Unknown error'));
    } finally {
      setExporting(false);
    }
  };

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
      {/* Header: Sub-tab navigation + actions */}
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

        <div className="flex items-center gap-2">
          {/* Export dropdown */}
          <div className="relative" ref={exportRef}>
            <button
              onClick={() => setExportOpen(!exportOpen)}
              disabled={exporting}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              {exporting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Download className="w-4 h-4" />
              )}
              Export
            </button>

            {exportOpen && (
              <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-20">
                <button
                  onClick={handleExportPdf}
                  className="flex items-center gap-3 w-full px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 text-left"
                >
                  <FileText className="w-4 h-4 text-red-500" />
                  <div>
                    <div className="font-medium">Export PDF</div>
                    <div className="text-xs text-gray-400">Full branded report</div>
                  </div>
                </button>
                <button
                  onClick={() => handleExportCsv('page_audits')}
                  className="flex items-center gap-3 w-full px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 text-left"
                >
                  <Table className="w-4 h-4 text-green-500" />
                  <div>
                    <div className="font-medium">CSV - Page Audits</div>
                    <div className="text-xs text-gray-400">Per-page scores and checks</div>
                  </div>
                </button>
                <button
                  onClick={() => handleExportCsv('findings')}
                  className="flex items-center gap-3 w-full px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 text-left"
                >
                  <Table className="w-4 h-4 text-blue-500" />
                  <div>
                    <div className="font-medium">CSV - Findings</div>
                    <div className="text-xs text-gray-400">All issues with severity</div>
                  </div>
                </button>
              </div>
            )}
          </div>

          {/* Regenerate button */}
          <button
            onClick={onGenerateReport}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Regenerate
          </button>
        </div>
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
