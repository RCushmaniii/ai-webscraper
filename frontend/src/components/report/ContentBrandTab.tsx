import React, { useState } from 'react';
import { Brain, Target, MessageSquare, List, Clock, AlertTriangle, Clipboard, Check } from 'lucide-react';
import { CrawlReport } from '../../services/api';

interface ContentBrandTabProps {
  report: CrawlReport;
}

const scoreColor = (score: number) =>
  score >= 70 ? 'text-green-600' : score >= 50 ? 'text-yellow-600' : 'text-red-600';

type SemanticStrategy = NonNullable<NonNullable<CrawlReport['report']>['semantic_strategy']>;

// Serialize the messaging review into clean plain text, ready to paste into
// an AI assistant. Only notes that quote real page copy are included.
const buildStrategyText = (strategy: SemanticStrategy, siteUrl?: string): string => {
  const lines: string[] = [];
  lines.push(`# Messaging review (AI reading, not a score)${siteUrl ? ` — ${siteUrl}` : ''}`);
  lines.push(
    `Headings, paragraph openers and CTA labels across ${strategy.pages_analyzed} pages. ` +
      'Each note is kept only when the AI quotes copy that is actually on the page.',
  );
  lines.push('');

  strategy.page_analyses.forEach((p) => {
    const a = p.analysis;
    lines.push(`## ${p.purpose.replace(/_/g, ' ')} — ${p.url}`);
    if (!a.evidence_verified) {
      lines.push('No verifiable note: the AI quoted nothing from this page, so its opinions were dropped.');
      lines.push('');
      lines.push('---');
      lines.push('');
      return;
    }
    if (a.evidence?.length) {
      lines.push('Reacting to:');
      a.evidence.forEach((q) => lines.push(`> ${q}`));
    }
    if (a.top_recommendation) lines.push(`Top recommendation: ${a.top_recommendation}`);
    lines.push('');

    lines.push('Intent alignment');
    if (a.intent_gap.assessment) lines.push(a.intent_gap.assessment);
    if (a.intent_gap.gaps.length) {
      lines.push('Gaps:');
      a.intent_gap.gaps.forEach((g) => lines.push(`- ${g}`));
    }
    if (a.intent_gap.suggestions.length) {
      lines.push('Suggestions:');
      a.intent_gap.suggestions.forEach((sug) => lines.push(`- ${sug}`));
    }
    lines.push('');

    lines.push('Tone & persona');
    if (a.tone_audit.detected_tone) lines.push(`Detected tone: ${a.tone_audit.detected_tone}`);
    if (a.tone_audit.audience_fit) lines.push(a.tone_audit.audience_fit);
    if (a.tone_audit.issues.length) {
      lines.push('Issues:');
      a.tone_audit.issues.forEach((i) => lines.push(`- ${i}`));
    }
    lines.push('');

    lines.push('Skim test');
    if (a.skim_test.story_assessment) lines.push(a.skim_test.story_assessment);
    if (a.skim_test.missing_beats.length) {
      lines.push('Missing beats:');
      a.skim_test.missing_beats.forEach((b) => lines.push(`- ${b}`));
    }
    if (a.skim_test.rewrite_suggestions.length) {
      lines.push('Heading rewrites:');
      a.skim_test.rewrite_suggestions.forEach((sug) => lines.push(`- ${sug}`));
    }

    if (a.suggested_title || a.suggested_meta) {
      lines.push('');
      lines.push('Suggested fixes:');
      if (a.suggested_title) lines.push(`- Title: ${a.suggested_title}`);
      if (a.suggested_meta) lines.push(`- Meta: ${a.suggested_meta}`);
    }

    lines.push('');
    lines.push('---');
    lines.push('');
  });

  return lines.join('\n').trim();
};

// Copy-to-clipboard button with transient "Copied" feedback.
const CopyButton: React.FC<{ text: string; label: string }> = ({ text, label }) => {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => {
        navigator.clipboard?.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }}
      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md border border-purple-300 text-purple-700 hover:bg-purple-50 transition-colors"
      aria-label={label}
    >
      {copied ? <Check className="w-3.5 h-3.5 text-green-600" /> : <Clipboard className="w-3.5 h-3.5" />}
      {copied ? 'Copied' : label}
    </button>
  );
};

const ContentBrandTab: React.FC<ContentBrandTabProps> = ({ report }) => {
  const r = report.report;
  if (!r) return null;

  return (
    <div className="space-y-6">
      {/* AI Narrative Header */}
      <div className="bg-gradient-to-r from-secondary-50 to-primary-50 rounded-lg border border-secondary-200 p-6">
        <h3 className="text-lg font-semibold text-secondary-900 mb-1 flex items-center gap-2">
          <Brain className="w-5 h-5" />
          Behind the Numbers
        </h3>
        <p className="text-sm text-secondary-600 mb-4">AI-powered narrative analysis of your audit data</p>
      </div>

      {/* Messaging review: an AI reading with its evidence attached, never a score */}
      {r.semantic_strategy?.page_analyses && r.semantic_strategy.page_analyses.length > 0 && (
        <div className="bg-white rounded-lg border border-purple-200 p-6">
          <div className="flex items-start justify-between gap-4 mb-4">
            <div>
              <h3 className="text-lg font-semibold text-purple-900 flex items-center gap-2">
                <Target className="w-5 h-5" />
                Messaging Review
                <span className="text-xs font-medium uppercase tracking-wide text-purple-700 bg-purple-100 rounded px-1.5 py-0.5">
                  AI reading, not a score
                </span>
              </h3>
              <p className="text-sm text-purple-600 mt-1">
                An AI read the headings, paragraph openers and CTA labels of {r.semantic_strategy.pages_analyzed} pages.
                A note is shown only when it quotes copy that is actually on the page; everything else was dropped.
                {typeof r.semantic_strategy.pages_with_evidence === 'number' && (
                  <> {r.semantic_strategy.pages_with_evidence} of {r.semantic_strategy.pages_analyzed} pages have a note.</>
                )}
              </p>
            </div>
            <div className="flex-shrink-0">
              <CopyButton
                text={buildStrategyText(r.semantic_strategy, r.site_url)}
                label="Copy section"
              />
            </div>
          </div>

          <div className="space-y-3">
            {r.semantic_strategy.page_analyses.map((pageAnalysis, index) => {
              const a = pageAnalysis.analysis;
              const verified = Boolean(a.evidence_verified);
              return (
              <details key={index} className="group border border-purple-100 rounded-lg">
                <summary className="flex items-center justify-between p-4 cursor-pointer hover:bg-purple-50 rounded-lg">
                  <div className="flex items-center gap-3 min-w-0">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                      pageAnalysis.purpose === 'lead_generation' ? 'bg-orange-100 text-orange-800' :
                      pageAnalysis.purpose === 'pricing' ? 'bg-amber-100 text-amber-800' :
                      pageAnalysis.purpose === 'homepage' ? 'bg-blue-100 text-blue-800' :
                      pageAnalysis.purpose === 'services' ? 'bg-green-100 text-green-800' :
                      pageAnalysis.purpose === 'educational' ? 'bg-secondary-100 text-secondary-800' :
                      pageAnalysis.purpose === 'portfolio' ? 'bg-indigo-100 text-indigo-800' :
                      pageAnalysis.purpose === 'brand_story' ? 'bg-pink-100 text-pink-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {pageAnalysis.purpose.replace(/_/g, ' ')}
                    </span>
                    <span className="text-sm font-medium text-gray-900 truncate">{pageAnalysis.url}</span>
                  </div>
                  <div className="ml-4 flex-shrink-0 text-xs">
                    {verified ? (
                      <span className="text-purple-700">
                        {a.evidence?.length} quote{a.evidence?.length === 1 ? '' : 's'} from the page
                      </span>
                    ) : (
                      <span className="text-gray-400">no verifiable note</span>
                    )}
                  </div>
                </summary>

                <div className="px-4 pb-4 space-y-4 border-t border-purple-100 pt-4">
                  {!verified ? (
                    <p className="text-sm text-gray-500">
                      The AI quoted nothing from this page, so its opinions were dropped rather than shown.
                    </p>
                  ) : (
                    <>
                      {/* Evidence: the lines the notes react to */}
                      {a.evidence && a.evidence.length > 0 && (
                        <div className="space-y-1">
                          <div className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Reacting to</div>
                          {a.evidence.map((quote, i) => (
                            <blockquote key={i} className="text-sm text-gray-800 pl-3 border-l-2 border-purple-300 italic">
                              {quote}
                            </blockquote>
                          ))}
                        </div>
                      )}

                      {/* Top Recommendation */}
                      {a.top_recommendation && (
                        <div className="bg-purple-50 rounded-lg p-3">
                          <div className="text-xs font-semibold text-purple-700 uppercase tracking-wide mb-1">Top Recommendation</div>
                          <div className="text-sm text-purple-900">{a.top_recommendation}</div>
                        </div>
                      )}

                      {/* Three Analysis Columns */}
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* Intent Gap */}
                        <div className="space-y-2">
                          <div className="text-xs font-semibold text-gray-700 uppercase tracking-wide flex items-center gap-1">
                            <Target className="w-3.5 h-3.5" /> Intent Alignment
                          </div>
                          <p className="text-xs text-gray-600">{a.intent_gap.assessment}</p>
                          {a.intent_gap.gaps.length > 0 && (
                            <div className="space-y-1">
                              <div className="text-xs font-medium text-red-700">Gaps:</div>
                              {a.intent_gap.gaps.map((gap, i) => (
                                <div key={i} className="text-xs text-red-600 pl-2 border-l-2 border-red-200">{gap}</div>
                              ))}
                            </div>
                          )}
                          {a.intent_gap.suggestions.length > 0 && (
                            <div className="space-y-1">
                              <div className="text-xs font-medium text-green-700">Suggestions:</div>
                              {a.intent_gap.suggestions.map((sug, i) => (
                                <div key={i} className="text-xs text-green-600 pl-2 border-l-2 border-green-200">{sug}</div>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Tone Audit */}
                        <div className="space-y-2">
                          <div className="text-xs font-semibold text-gray-700 uppercase tracking-wide flex items-center gap-1">
                            <MessageSquare className="w-3.5 h-3.5" /> Tone & Persona
                          </div>
                          <div className="text-xs">
                            <span className="text-gray-500">Detected:</span>{' '}
                            <span className="font-medium text-gray-900">{a.tone_audit.detected_tone}</span>
                          </div>
                          <p className="text-xs text-gray-600">{a.tone_audit.audience_fit}</p>
                          {a.tone_audit.issues.length > 0 && (
                            <div className="space-y-1">
                              <div className="text-xs font-medium text-yellow-700">Issues:</div>
                              {a.tone_audit.issues.map((issue, i) => (
                                <div key={i} className="text-xs text-yellow-600 pl-2 border-l-2 border-yellow-200">{issue}</div>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Skim Test */}
                        <div className="space-y-2">
                          <div className="text-xs font-semibold text-gray-700 uppercase tracking-wide flex items-center gap-1">
                            <List className="w-3.5 h-3.5" /> Skim Test
                          </div>
                          <p className="text-xs text-gray-600">{a.skim_test.story_assessment}</p>
                          {a.skim_test.missing_beats.length > 0 && (
                            <div className="space-y-1">
                              <div className="text-xs font-medium text-orange-700">Missing beats:</div>
                              {a.skim_test.missing_beats.map((beat, i) => (
                                <div key={i} className="text-xs text-orange-600 pl-2 border-l-2 border-orange-200">{beat}</div>
                              ))}
                            </div>
                          )}
                          {a.skim_test.rewrite_suggestions.length > 0 && (
                            <div className="space-y-1">
                              <div className="text-xs font-medium text-blue-700">Heading rewrites:</div>
                              {a.skim_test.rewrite_suggestions.map((sug, i) => (
                                <div key={i} className="text-xs text-blue-600 pl-2 border-l-2 border-blue-200">{sug}</div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Suggested Fixes */}
                      {(a.suggested_title || a.suggested_meta) && (
                        <div className="bg-green-50 rounded-lg p-3 space-y-2">
                          <div className="text-xs font-semibold text-green-700 uppercase tracking-wide">Suggested Fixes</div>
                          {a.suggested_title && (
                            <div className="text-xs">
                              <span className="font-medium text-green-800">Title:</span>{' '}
                              <span className="text-green-700">{a.suggested_title}</span>
                            </div>
                          )}
                          {a.suggested_meta && (
                            <div className="text-xs">
                              <span className="font-medium text-green-800">Meta:</span>{' '}
                              <span className="text-green-700">{a.suggested_meta}</span>
                            </div>
                          )}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </details>
              );
            })}
          </div>
        </div>
      )}

      {/* Content Freshness Analysis */}
      {r.content_freshness && r.content_freshness.pages_with_dates > 0 && (() => {
        const cf = r.content_freshness;
        const scoreBg = cf.freshness_score >= 70 ? 'border-green-200 bg-green-50'
          : cf.freshness_score >= 50 ? 'border-yellow-200 bg-yellow-50'
          : 'border-red-200 bg-red-50';
        return (
          <div className={`rounded-lg border p-6 ${scoreBg}`}>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <Clock className="w-5 h-5" />
                  Content Freshness
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  {cf.pages_with_dates} of {r.metrics?.total_pages || '?'} pages have detectable dates
                  ({cf.date_coverage_pct}% coverage)
                </p>
              </div>
              <div className="text-right">
                <div className={`text-4xl font-bold ${scoreColor(cf.freshness_score)}`}>
                  {cf.freshness_score}
                </div>
                <div className="text-xs text-gray-500">out of 100</div>
              </div>
            </div>

            {/* Key Stats */}
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="text-center p-3 rounded-lg bg-white/60 border border-gray-100">
                <div className="text-2xl font-bold text-gray-900">{cf.recent_count}</div>
                <div className="text-xs text-gray-500">Recent (&lt;90 days)</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-white/60 border border-gray-100">
                <div className="text-2xl font-bold text-gray-900">{cf.avg_age_days !== null ? `${cf.avg_age_days}d` : '—'}</div>
                <div className="text-xs text-gray-500">Average Age</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-white/60 border border-gray-100">
                <div className={`text-2xl font-bold ${cf.stale_count > 0 ? 'text-red-600' : 'text-green-600'}`}>{cf.stale_count}</div>
                <div className="text-xs text-gray-500">Stale (&gt;1 year)</div>
              </div>
            </div>

            {/* Stale Pages Warning */}
            {cf.stale_pages && cf.stale_pages.length > 0 && (
              <div className="mt-4">
                <h4 className="text-sm font-medium text-red-700 mb-2 flex items-center gap-1">
                  <AlertTriangle className="w-4 h-4" />
                  Stale Content (oldest first)
                </h4>
                <div className="space-y-1.5">
                  {cf.stale_pages.map((page, i) => (
                    <div key={i} className="flex items-center justify-between py-2 px-3 bg-white/70 rounded border border-red-100 text-sm">
                      <div className="min-w-0">
                        <a href={page.url} target="_blank" rel="noopener noreferrer" className="text-secondary-600 hover:underline truncate block max-w-xs">
                          {page.url.replace(/^https?:\/\/[^/]+/, '') || '/'}
                        </a>
                        {page.title && page.title !== 'Untitled' && (
                          <span className="text-xs text-gray-400">{page.title}</span>
                        )}
                      </div>
                      <div className="text-xs text-gray-500 flex-shrink-0 ml-4">
                        {page.date} ({Math.round(page.days_old / 30)}mo ago)
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      })()}
    </div>
  );
};

export default ContentBrandTab;
