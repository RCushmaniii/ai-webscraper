import React from "react";
import {
  AlertTriangle,
  Zap,
  TrendingUp,
  Clock,
  Target,
  Clipboard,
  Check,
  CheckCircle2,
} from "lucide-react";
import { CrawlReport } from "../../services/api";

interface ExecutiveTabProps {
  report: CrawlReport;
}

const scoreColor = (score: number) =>
  score >= 80
    ? "text-green-600"
    : score >= 60
      ? "text-yellow-600"
      : "text-red-600";

const rateColor = (rate: number) =>
  rate >= 80
    ? "text-green-600"
    : rate >= 50
      ? "text-yellow-600"
      : "text-red-600";

const priorityBadge = (p: string) =>
  p === "critical"
    ? "bg-red-100 text-red-800 border-red-300"
    : p === "high"
      ? "bg-orange-100 text-orange-800 border-orange-300"
      : "bg-yellow-100 text-yellow-800 border-yellow-300";

// Small copy-to-clipboard button — reinforces the "copy-paste fixes" promise.
const CopyButton: React.FC<{ text: string }> = ({ text }) => {
  const [copied, setCopied] = React.useState(false);
  return (
    <button
      onClick={() => {
        navigator.clipboard?.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }}
      className="flex-shrink-0 inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-md border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors"
      aria-label="Copy fix to clipboard"
    >
      {copied ? (
        <Check className="w-3.5 h-3.5 text-green-600" />
      ) : (
        <Clipboard className="w-3.5 h-3.5" />
      )}
      {copied ? "Copied" : "Copy"}
    </button>
  );
};

const ExecutiveTab: React.FC<ExecutiveTabProps> = ({ report }) => {
  const r = report.report;
  if (!r) return null;

  const exec = r.executive_summary;
  const criticalIssues = exec?.critical_issues ?? [];
  const quickWins = exec?.quick_wins ?? [];
  const strategicRecs = exec?.strategic_recommendations ?? [];
  const noFindings =
    criticalIssues.length === 0 &&
    quickWins.length === 0 &&
    strategicRecs.length === 0;

  return (
    <div className="space-y-6">
      {/* Health Score Overview */}
      <div className="bg-gradient-to-r from-secondary-50 to-blue-50 rounded-xl p-6 border border-secondary-100">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              Site Health Score
            </h3>
            <p className="text-gray-600">{exec?.one_line_summary}</p>
          </div>
          <div className="text-right flex-shrink-0">
            <div
              className={`text-5xl font-bold ${scoreColor(exec?.site_health_score || 0)}`}
            >
              {exec?.site_health_score || 0}
            </div>
            <div className="text-sm text-gray-500">out of 100</div>
          </div>
        </div>
      </div>

      {/* ── THE TREATMENT PLAN (leads the report) ─────────────────────── */}

      {/* Critical Issues */}
      {criticalIssues.length > 0 && (
        <div>
          <h3 className="flex items-center gap-2 text-lg font-semibold text-gray-900 mb-3">
            <AlertTriangle className="w-5 h-5 text-red-600" />
            Critical Issues — fix these first
          </h3>
          <div className="space-y-3">
            {criticalIssues.map((issue, i) => (
              <div
                key={i}
                className="bg-white rounded-lg border border-red-200 p-5"
              >
                <div className="flex items-start justify-between gap-3 mb-2">
                  <h4 className="font-semibold text-gray-900">{issue.title}</h4>
                  <span
                    className={`flex-shrink-0 px-2 py-0.5 text-xs font-semibold rounded-full border ${priorityBadge(issue.priority)}`}
                  >
                    {issue.priority}
                  </span>
                </div>
                <p className="text-sm text-gray-700 mb-3">
                  {issue.description}
                </p>
                <div className="bg-red-50 border border-red-100 rounded-md p-3">
                  <span className="text-xs font-semibold text-red-800 uppercase tracking-wide">
                    Fix
                  </span>
                  <p className="text-sm text-gray-800 mt-1">
                    {issue.recommended_action}
                  </p>
                </div>
                {issue.pages_affected > 0 && (
                  <div className="text-xs text-gray-500 mt-2">
                    {issue.pages_affected} page
                    {issue.pages_affected !== 1 ? "s" : ""} affected
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Wins */}
      {quickWins.length > 0 && (
        <div>
          <h3 className="flex items-center gap-2 text-lg font-semibold text-gray-900 mb-3">
            <Zap className="w-5 h-5 text-green-600" />
            Quick Wins — copy-paste fixes
          </h3>
          <div className="space-y-2">
            {quickWins.map((win, i) => (
              <div
                key={i}
                className="flex items-start justify-between gap-3 bg-green-50 border border-green-200 rounded-lg p-4"
              >
                <p className="text-sm text-gray-800">{win}</p>
                <CopyButton text={win} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Strategic Recommendations */}
      {strategicRecs.length > 0 && (
        <div>
          <h3 className="flex items-center gap-2 text-lg font-semibold text-gray-900 mb-3">
            <TrendingUp className="w-5 h-5 text-secondary-600" />
            Strategic Recommendations
          </h3>
          <div className="space-y-3">
            {strategicRecs.map((rec, i) => (
              <div
                key={i}
                className="bg-white rounded-lg border border-gray-200 p-5"
              >
                <h4 className="font-semibold text-gray-900 mb-1">
                  {rec.title}
                </h4>
                <p className="text-sm text-gray-700 mb-3">{rec.description}</p>
                <div className="flex flex-wrap gap-2">
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-800 border border-blue-200">
                    <Target className="w-3.5 h-3.5" /> Impact:{" "}
                    {rec.expected_impact}
                  </span>
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-purple-50 text-purple-800 border border-purple-200">
                    <Clock className="w-3.5 h-3.5" /> Effort:{" "}
                    {rec.effort_estimate}
                  </span>
                  {rec.timeline && (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700 border border-gray-200">
                      {rec.timeline}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Clean bill of health (perfect-score case) */}
      {noFindings && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 flex items-start gap-3">
          <CheckCircle2 className="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-lg font-semibold text-green-800 mb-1">
              No critical issues or quick wins found
            </h3>
            <p className="text-gray-700 text-sm">
              This site passed the automated checks cleanly. See the strategic
              recommendations and the detailed metrics below for opportunities
              to push further.
            </p>
          </div>
        </div>
      )}

      {/* Action Plan (prose roadmap) */}
      {exec?.action_plan_summary && (
        <div className="bg-secondary-50 rounded-lg border border-secondary-200 p-6">
          <h3 className="text-lg font-semibold text-secondary-900 mb-3">
            Recommended Action Plan
          </h3>
          <p className="text-gray-700">{exec.action_plan_summary}</p>
        </div>
      )}

      {/* Strengths & Weaknesses */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg border border-green-200 p-6">
          <h3 className="text-lg font-semibold text-green-800 mb-3">
            Strengths
          </h3>
          <p className="text-gray-700">
            {exec?.strengths_summary || "No strengths summary available."}
          </p>
        </div>
        <div className="bg-white rounded-lg border border-orange-200 p-6">
          <h3 className="text-lg font-semibold text-orange-800 mb-3">
            Areas for Improvement
          </h3>
          <p className="text-gray-700">
            {exec?.weaknesses_summary || "No weaknesses summary available."}
          </p>
        </div>
      </div>

      {/* ── DETAILED METRICS (the diagnostic data, demoted below the plan) ── */}
      <div className="pt-4 border-t border-gray-200">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-400 mb-4">
          Detailed Metrics
        </h3>

        {/* Score Breakdown */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {[
            { label: "Technical SEO", score: exec?.technical_seo_score },
            { label: "Content Quality", score: exec?.content_quality_score },
            { label: "User Experience", score: exec?.user_experience_score },
            { label: "Trust Signals", score: exec?.trust_signals_score },
          ].map((item) => (
            <div
              key={item.label}
              className="bg-white rounded-lg border border-gray-200 p-4"
            >
              <div className="text-sm text-gray-600 mb-1">{item.label}</div>
              <div
                className={`text-2xl font-bold ${scoreColor(item.score || 0)}`}
              >
                {item.score || 0}
              </div>
            </div>
          ))}
        </div>

        {/* Crawl Metrics */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h4 className="font-semibold text-gray-900 mb-4">Crawl Metrics</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {r.metrics?.total_pages || 0}
              </div>
              <div className="text-sm text-gray-500">Pages Crawled</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {r.metrics?.total_issues || 0}
              </div>
              <div className="text-sm text-gray-500">Total Issues</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {r.metrics?.broken_links || 0}
              </div>
              <div className="text-sm text-gray-500">Broken Links</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {r.metrics?.missing_meta || 0}
              </div>
              <div className="text-sm text-gray-500">Missing Meta</div>
            </div>
          </div>
        </div>

        {/* SEO Pass Rates */}
        {r.summary_stats && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h4 className="font-semibold text-gray-900 mb-4">SEO Pass Rates</h4>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {[
                {
                  label: "Title Tags",
                  rate: r.summary_stats.title_pass_rate,
                  target: "30-60 chars",
                },
                {
                  label: "Meta Descriptions",
                  rate: r.summary_stats.meta_pass_rate,
                  target: "120-160 chars",
                },
                {
                  label: "H1 Tags",
                  rate: r.summary_stats.h1_pass_rate,
                  target: "Present",
                },
                {
                  label: "Content Depth",
                  rate: r.summary_stats.content_pass_rate,
                  target: "300+ words",
                },
                {
                  label: "Response Time",
                  rate: r.summary_stats.performance_pass_rate,
                  target: "<1000ms",
                },
              ].map((item) => (
                <div key={item.label} className="text-center">
                  <div className={`text-2xl font-bold ${rateColor(item.rate)}`}>
                    {item.rate}%
                  </div>
                  <div className="text-sm font-medium text-gray-700">
                    {item.label}
                  </div>
                  <div className="text-xs text-gray-400">{item.target}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExecutiveTab;
