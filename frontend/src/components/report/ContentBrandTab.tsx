import React from 'react';
import { Brain, Target, MessageSquare, List } from 'lucide-react';
import { CrawlReport } from '../../services/api';

interface ContentBrandTabProps {
  report: CrawlReport;
}

const scoreColor = (score: number) =>
  score >= 70 ? 'text-green-600' : score >= 50 ? 'text-yellow-600' : 'text-red-600';

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

      {/* Strategy & Conversion Analysis */}
      {r.semantic_strategy?.page_analyses && r.semantic_strategy.page_analyses.length > 0 && (
        <div className="bg-white rounded-lg border border-purple-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-purple-900 flex items-center gap-2">
                <Target className="w-5 h-5" />
                Strategy & Conversion Analysis
              </h3>
              <p className="text-sm text-purple-600 mt-1">
                AI-evaluated messaging, intent alignment, and persuasion structure across {r.semantic_strategy.pages_analyzed} pages
              </p>
            </div>
            {r.semantic_strategy.avg_strategy_score !== null && (
              <div className={`text-2xl font-bold ${scoreColor(r.semantic_strategy.avg_strategy_score)}`}>
                {r.semantic_strategy.avg_strategy_score}/100
              </div>
            )}
          </div>

          <div className="space-y-3">
            {r.semantic_strategy.page_analyses.map((pageAnalysis, index) => (
              <details key={index} className="group border border-purple-100 rounded-lg">
                <summary className="flex items-center justify-between p-4 cursor-pointer hover:bg-purple-50 rounded-lg">
                  <div className="flex items-center gap-3 min-w-0">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                      pageAnalysis.purpose === 'lead_generation' ? 'bg-orange-100 text-orange-800' :
                      pageAnalysis.purpose === 'homepage' ? 'bg-blue-100 text-blue-800' :
                      pageAnalysis.purpose === 'services' ? 'bg-green-100 text-green-800' :
                      pageAnalysis.purpose === 'educational' ? 'bg-teal-100 text-teal-800' :
                      pageAnalysis.purpose === 'portfolio' ? 'bg-indigo-100 text-indigo-800' :
                      pageAnalysis.purpose === 'brand_story' ? 'bg-pink-100 text-pink-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {pageAnalysis.purpose.replace(/_/g, ' ')}
                    </span>
                    <span className="text-sm font-medium text-gray-900 truncate">{pageAnalysis.url}</span>
                  </div>
                  <div className="flex items-center gap-4 ml-4 flex-shrink-0">
                    <div className="flex items-center gap-3 text-xs text-gray-500">
                      <span title="Intent alignment">
                        <Target className="w-3.5 h-3.5 inline mr-1" />
                        {pageAnalysis.analysis.intent_gap.alignment_score}
                      </span>
                      <span title="Tone match">
                        <MessageSquare className="w-3.5 h-3.5 inline mr-1" />
                        {pageAnalysis.analysis.tone_audit.tone_match_score}
                      </span>
                      <span title="Skim test">
                        <List className="w-3.5 h-3.5 inline mr-1" />
                        {pageAnalysis.analysis.skim_test.skim_score}
                      </span>
                    </div>
                    <span className={`text-sm font-bold ${scoreColor(pageAnalysis.analysis.overall_strategy_score)}`}>
                      {pageAnalysis.analysis.overall_strategy_score}/100
                    </span>
                  </div>
                </summary>

                <div className="px-4 pb-4 space-y-4 border-t border-purple-100 pt-4">
                  {/* Top Recommendation */}
                  <div className="bg-purple-50 rounded-lg p-3">
                    <div className="text-xs font-semibold text-purple-700 uppercase tracking-wide mb-1">Top Recommendation</div>
                    <div className="text-sm text-purple-900">{pageAnalysis.analysis.top_recommendation}</div>
                  </div>

                  {/* Three Analysis Columns */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Intent Gap */}
                    <div className="space-y-2">
                      <div className="text-xs font-semibold text-gray-700 uppercase tracking-wide flex items-center gap-1">
                        <Target className="w-3.5 h-3.5" /> Intent Alignment
                        <span className={`ml-auto text-sm font-bold ${scoreColor(pageAnalysis.analysis.intent_gap.alignment_score)}`}>
                          {pageAnalysis.analysis.intent_gap.alignment_score}
                        </span>
                      </div>
                      <p className="text-xs text-gray-600">{pageAnalysis.analysis.intent_gap.assessment}</p>
                      {pageAnalysis.analysis.intent_gap.gaps.length > 0 && (
                        <div className="space-y-1">
                          <div className="text-xs font-medium text-red-700">Gaps:</div>
                          {pageAnalysis.analysis.intent_gap.gaps.map((gap, i) => (
                            <div key={i} className="text-xs text-red-600 pl-2 border-l-2 border-red-200">{gap}</div>
                          ))}
                        </div>
                      )}
                      {pageAnalysis.analysis.intent_gap.suggestions.length > 0 && (
                        <div className="space-y-1">
                          <div className="text-xs font-medium text-green-700">Suggestions:</div>
                          {pageAnalysis.analysis.intent_gap.suggestions.map((sug, i) => (
                            <div key={i} className="text-xs text-green-600 pl-2 border-l-2 border-green-200">{sug}</div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Tone Audit */}
                    <div className="space-y-2">
                      <div className="text-xs font-semibold text-gray-700 uppercase tracking-wide flex items-center gap-1">
                        <MessageSquare className="w-3.5 h-3.5" /> Tone & Persona
                        <span className={`ml-auto text-sm font-bold ${scoreColor(pageAnalysis.analysis.tone_audit.tone_match_score)}`}>
                          {pageAnalysis.analysis.tone_audit.tone_match_score}
                        </span>
                      </div>
                      <div className="text-xs">
                        <span className="text-gray-500">Detected:</span>{' '}
                        <span className="font-medium text-gray-900">{pageAnalysis.analysis.tone_audit.detected_tone}</span>
                      </div>
                      <p className="text-xs text-gray-600">{pageAnalysis.analysis.tone_audit.audience_fit}</p>
                      {pageAnalysis.analysis.tone_audit.issues.length > 0 && (
                        <div className="space-y-1">
                          <div className="text-xs font-medium text-yellow-700">Issues:</div>
                          {pageAnalysis.analysis.tone_audit.issues.map((issue, i) => (
                            <div key={i} className="text-xs text-yellow-600 pl-2 border-l-2 border-yellow-200">{issue}</div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Skim Test */}
                    <div className="space-y-2">
                      <div className="text-xs font-semibold text-gray-700 uppercase tracking-wide flex items-center gap-1">
                        <List className="w-3.5 h-3.5" /> Skim Test
                        <span className={`ml-auto text-sm font-bold ${scoreColor(pageAnalysis.analysis.skim_test.skim_score)}`}>
                          {pageAnalysis.analysis.skim_test.skim_score}
                        </span>
                      </div>
                      <p className="text-xs text-gray-600">{pageAnalysis.analysis.skim_test.story_assessment}</p>
                      {pageAnalysis.analysis.skim_test.missing_beats.length > 0 && (
                        <div className="space-y-1">
                          <div className="text-xs font-medium text-orange-700">Missing beats:</div>
                          {pageAnalysis.analysis.skim_test.missing_beats.map((beat, i) => (
                            <div key={i} className="text-xs text-orange-600 pl-2 border-l-2 border-orange-200">{beat}</div>
                          ))}
                        </div>
                      )}
                      {pageAnalysis.analysis.skim_test.rewrite_suggestions.length > 0 && (
                        <div className="space-y-1">
                          <div className="text-xs font-medium text-blue-700">Heading rewrites:</div>
                          {pageAnalysis.analysis.skim_test.rewrite_suggestions.map((sug, i) => (
                            <div key={i} className="text-xs text-blue-600 pl-2 border-l-2 border-blue-200">{sug}</div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Suggested Fixes */}
                  {(pageAnalysis.analysis.suggested_title || pageAnalysis.analysis.suggested_meta) && (
                    <div className="bg-green-50 rounded-lg p-3 space-y-2">
                      <div className="text-xs font-semibold text-green-700 uppercase tracking-wide">Suggested Fixes</div>
                      {pageAnalysis.analysis.suggested_title && (
                        <div className="text-xs">
                          <span className="font-medium text-green-800">Title:</span>{' '}
                          <span className="text-green-700">{pageAnalysis.analysis.suggested_title}</span>
                        </div>
                      )}
                      {pageAnalysis.analysis.suggested_meta && (
                        <div className="text-xs">
                          <span className="font-medium text-green-800">Meta:</span>{' '}
                          <span className="text-green-700">{pageAnalysis.analysis.suggested_meta}</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </details>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ContentBrandTab;
