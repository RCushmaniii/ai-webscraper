import React from "react";
import { Gauge } from "lucide-react";
import type { PageSpeedData, PageSpeedResult } from "../../services/api";

/**
 * Google PageSpeed Insights (Lighthouse) results for the start page and the
 * top pages. This is the visitor-side performance measurement the report
 * quotes; the per-page "Server" column is only server time to first byte
 * from our own server.
 */

const scoreTone = (score: number | null | undefined) => {
  if (score == null) return "text-gray-400 border-gray-200";
  if (score >= 90) return "text-green-700 border-green-500";
  if (score >= 50) return "text-yellow-700 border-yellow-500";
  return "text-red-700 border-red-500";
};

const fmtMs = (ms: number | null | undefined) => {
  if (ms == null) return "n/a";
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)} s` : `${ms} ms`;
};

const pathOf = (url: string) => url.replace(/^https?:\/\/[^/]+/, "") || "/";

const ScoreRing: React.FC<{ score: number | null | undefined }> = ({
  score,
}) => (
  <div
    className={`w-14 h-14 rounded-full border-4 flex items-center justify-center text-lg font-bold ${scoreTone(score)}`}
    aria-label={
      score == null ? "No score" : `Performance score ${score} of 100`
    }
  >
    {score == null ? "–" : score}
  </div>
);

const Metric: React.FC<{ label: string; value: string; title: string }> = ({
  label,
  value,
  title,
}) => (
  <div className="text-center" title={title}>
    <div className="text-sm font-semibold text-gray-900">{value}</div>
    <div className="text-xs text-gray-500">{label}</div>
  </div>
);

const ResultRow: React.FC<{ result: PageSpeedResult }> = ({ result }) => (
  <div className="flex items-center gap-4 py-3 border-b border-gray-100 last:border-b-0">
    <ScoreRing score={result.performance_score} />
    <div className="flex-1 min-w-0">
      <div className="flex items-center gap-2">
        <a
          href={result.url}
          target="_blank"
          rel="noopener noreferrer"
          className="font-medium text-gray-900 truncate hover:underline"
          title={result.url}
        >
          {pathOf(result.url)}
        </a>
        <span className="text-xs uppercase tracking-wide text-gray-500 bg-gray-100 rounded px-1.5 py-0.5">
          {result.strategy}
        </span>
      </div>
      <div className="mt-2 grid grid-cols-3 sm:grid-cols-5 gap-3">
        <Metric
          label="LCP"
          value={fmtMs(result.lcp_ms)}
          title="Largest Contentful Paint: when the main content is visible"
        />
        <Metric
          label="CLS"
          value={result.cls == null ? "n/a" : String(result.cls)}
          title="Cumulative Layout Shift: how much the page moves while loading"
        />
        <Metric
          label="TBT"
          value={fmtMs(result.tbt_ms)}
          title="Total Blocking Time: how long scripts block interaction"
        />
        <Metric
          label="FCP"
          value={fmtMs(result.fcp_ms)}
          title="First Contentful Paint: when the first text or image appears"
        />
        <Metric
          label="TTFB"
          value={fmtMs(result.server_response_ms)}
          title="Server response time as measured by Google"
        />
      </div>
      {result.field && (
        <div className="mt-1 text-xs text-gray-500">
          Real-user Chrome data:{" "}
          <span className="font-medium">
            {result.field.overall_category?.toLowerCase() || "available"}
          </span>
          {result.field.lcp_ms != null &&
            ` · LCP ${fmtMs(result.field.lcp_ms)}`}
          {result.field.inp_ms != null &&
            ` · INP ${fmtMs(result.field.inp_ms)}`}
          {result.field.cls != null && ` · CLS ${result.field.cls}`}
        </div>
      )}
    </div>
  </div>
);

const PageSpeedCard: React.FC<{ pagespeed?: PageSpeedData | null }> = ({
  pagespeed,
}) => {
  const results = pagespeed?.results ?? [];
  const errors = pagespeed?.errors ?? [];
  if (results.length === 0 && errors.length === 0) return null;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-start justify-between gap-4 mb-2">
        <h4 className="flex items-center gap-2 font-semibold text-gray-900">
          <Gauge className="w-5 h-5 text-secondary-600" aria-hidden="true" />
          Performance (Google PageSpeed Insights)
        </h4>
        {pagespeed?.fetched_at && (
          <span className="text-xs text-gray-400">
            {new Date(pagespeed.fetched_at).toLocaleString()}
          </span>
        )}
      </div>
      <p className="text-sm text-gray-500 mb-2">
        Lighthouse scores from Google, the same test as PageSpeed Insights. 90
        and above is good.
      </p>
      {results.map((r) => (
        <ResultRow key={`${r.strategy}-${r.url}`} result={r} />
      ))}
      {errors.length > 0 && (
        <p className="mt-3 text-xs text-gray-400">
          {results.length === 0
            ? "Google could not audit this site during the crawl."
            : `${errors.length} page${errors.length === 1 ? "" : "s"} could not be audited by Google.`}
        </p>
      )}
    </div>
  );
};

export default PageSpeedCard;
