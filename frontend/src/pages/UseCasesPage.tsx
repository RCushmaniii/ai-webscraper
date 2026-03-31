import React from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle, ArrowRight, TrendingUp, Clock, DollarSign, Users, Zap, BarChart3, Target } from 'lucide-react';
import { usePageTitle } from '../hooks/usePageTitle';

const UseCasesPage: React.FC = () => {
  usePageTitle('Use Cases');
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-secondary-50 via-white to-primary-50 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
              How Teams Use AI WebScraper
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
              From SEO agencies scaling client work to small businesses optimizing their online presence —
              here's how different teams get value from AI-powered site analysis.
            </p>
            <p className="mt-4 text-sm text-gray-500 max-w-2xl mx-auto">
              The scenarios below are hypothetical examples based on common workflows. Actual results
              depend on your site size, traffic, and how central your website is to your business.
            </p>
          </div>
        </div>
      </section>

      {/* Use Case 1: SEO Agency */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-700 rounded-full text-sm font-medium mb-4">
                SEO Agency
              </div>
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
                Scale Client Audits Without Scaling Headcount
              </h2>
              <p className="text-lg text-gray-700 mb-6 leading-relaxed">
                Imagine an SEO agency that spends 15-20 hours per client audit — manually reviewing pages,
                checking meta tags, compiling spreadsheets. They can realistically handle a handful of clients per month
                before hitting capacity.
              </p>

              <div className="space-y-4 mb-8">
                <div className="flex items-start gap-3">
                  <Clock className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">The Bottleneck</h3>
                    <p className="text-gray-600">
                      Client sites typically run 200-500 pages. Manual review means clicking through every page,
                      taking notes, and assembling reports by hand. It's thorough, but it doesn't scale.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Zap className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">With AI WebScraper</h3>
                    <p className="text-gray-600">
                      The crawler maps the site, the issue detector flags problems, and the AI prioritizes
                      fixes by business impact — all within minutes. The analyst's time shifts from data gathering
                      to client strategy.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <TrendingUp className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">The Upside</h3>
                    <p className="text-gray-600">
                      When audit time drops significantly, the same team can serve more clients —
                      or spend more time on high-value strategy work that commands higher fees.
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <div className="text-sm font-medium text-blue-700 mb-3">Potential Impact</div>
                <ul className="space-y-2 text-sm text-gray-700">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                    <span>Reduce per-audit time from days to hours</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                    <span>Handle more clients without additional hires</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                    <span>Deliver AI-enhanced reports clients can act on immediately</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-8 border border-blue-200">
              <h3 className="text-xl font-semibold text-gray-900 mb-6">Hypothetical: Before vs After</h3>

              <div className="space-y-6">
                <div>
                  <div className="text-sm font-medium text-gray-500 mb-2">MANUAL WORKFLOW</div>
                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <ul className="space-y-2 text-sm text-gray-700">
                      <li>• 15-20 hours per audit</li>
                      <li>• Limited client capacity</li>
                      <li>• Spreadsheet-based reports</li>
                      <li>• Analyst time spent on data gathering</li>
                    </ul>
                  </div>
                </div>

                <div className="flex justify-center">
                  <ArrowRight className="w-6 h-6 text-blue-600" />
                </div>

                <div>
                  <div className="text-sm font-medium text-gray-500 mb-2">AI-ASSISTED WORKFLOW</div>
                  <div className="bg-white rounded-lg p-4 border border-green-200">
                    <ul className="space-y-2 text-sm text-gray-700">
                      <li className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        Crawl + analysis in minutes
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        More capacity per analyst
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        AI-prioritized, client-ready reports
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        Analyst time spent on strategy
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Use Case 2: Small Business Owner */}
      <section className="py-20 bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="order-2 lg:order-1">
              <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-8 border border-purple-200">
                <h3 className="text-xl font-semibold text-gray-900 mb-6">The Value Depends on Your Traffic</h3>

                <div className="space-y-4">
                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <div className="flex items-center gap-2 mb-2">
                      <BarChart3 className="w-5 h-5 text-purple-600" />
                      <span className="font-semibold text-gray-900 text-sm">High-Traffic Site (10k+ visits/mo)</span>
                    </div>
                    <p className="text-sm text-gray-600">
                      Your website is a major revenue driver. A 404 on a conversion page, a slow-loading
                      landing page, or missing meta data could be costing you real money every day. An audit
                      here can surface high-impact fixes quickly.
                    </p>
                  </div>

                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <div className="flex items-center gap-2 mb-2">
                      <BarChart3 className="w-5 h-5 text-purple-600" />
                      <span className="font-semibold text-gray-900 text-sm">Growing Site (1k-10k visits/mo)</span>
                    </div>
                    <p className="text-sm text-gray-600">
                      You're building momentum. Technical issues and SEO gaps at this stage can cap your growth
                      ceiling. Catching them early means your content investment compounds instead of stalling.
                    </p>
                  </div>

                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <div className="flex items-center gap-2 mb-2">
                      <BarChart3 className="w-5 h-5 text-purple-600" />
                      <span className="font-semibold text-gray-900 text-sm">New Site (Under 1k visits/mo)</span>
                    </div>
                    <p className="text-sm text-gray-600">
                      You want to make sure the foundation is solid before investing in content and marketing.
                      An audit catches structural issues early, when they're cheapest to fix.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="order-1 lg:order-2">
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-100 text-purple-700 rounded-full text-sm font-medium mb-4">
                Small Business Owner
              </div>
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
                Know What's Actually Wrong — Without the Jargon
              </h2>
              <p className="text-lg text-gray-700 mb-6 leading-relaxed">
                You built a website, or someone built it for you. It looks fine. But is it actually working
                for your business? Most small business owners don't have an SEO team — and hiring a consultant
                for a one-time audit can be expensive.
              </p>

              <div className="space-y-4 mb-8">
                <div className="flex items-start gap-3">
                  <Zap className="w-6 h-6 text-purple-600 flex-shrink-0 mt-1" />
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">Plain-English Recommendations</h3>
                    <p className="text-gray-600">
                      No technical jargon. Every issue comes with a clear explanation of why it matters
                      and what to do about it — tagged by whether it's a 5-minute fix or needs a developer.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Zap className="w-6 h-6 text-purple-600 flex-shrink-0 mt-1" />
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">Prioritized by Business Impact</h3>
                    <p className="text-gray-600">
                      Not all issues are equal. A broken link on your homepage matters more than a missing
                      alt tag on a footer image. The AI ranks everything so you know what to tackle first.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Zap className="w-6 h-6 text-purple-600 flex-shrink-0 mt-1" />
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">Effort Estimates on Every Fix</h3>
                    <p className="text-gray-600">
                      Know exactly what you can handle yourself and what to hand to a developer.
                      No more guessing about scope or cost.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Use Case 3: Content / Marketing Team */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-100 text-green-700 rounded-full text-sm font-medium mb-4">
                Content &amp; Marketing Team
              </div>
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
                Maintain Quality Across Hundreds of Pages
              </h2>
              <p className="text-lg text-gray-700 mb-6 leading-relaxed">
                As your site grows, content quality tends to drift. Pages get stale. Meta descriptions
                go missing. Brand voice shifts between authors. Manual review at scale is impractical —
                which is exactly where AI-powered analysis shines.
              </p>

              <div className="space-y-6">
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="font-semibold text-gray-900 mb-2">What the AI Catches</div>
                  <ul className="space-y-2 text-sm text-gray-700">
                    <li className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                      Missing or duplicate meta descriptions
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                      Thin content pages that may hurt SEO
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                      Heading structure issues (missing H1s, skipped levels)
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                      Broken internal and external links
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                      Brand voice inconsistencies across pages
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                      Images without alt text (accessibility gaps)
                    </li>
                  </ul>
                </div>

                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="font-semibold text-gray-900 mb-2">Why It Matters</div>
                  <p className="text-sm text-gray-700">
                    For sites where organic search is a significant traffic source, technical SEO issues
                    can silently cap your growth. A site with clean structure, consistent metadata, and
                    no broken paths gives search engines — and visitors — confidence in your content.
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-green-50 to-teal-50 rounded-2xl p-8 border border-green-200">
              <h3 className="text-xl font-semibold text-gray-900 mb-6">Hypothetical Workflow</h3>

              <div className="space-y-6">
                <div>
                  <div className="text-sm font-medium text-gray-500 mb-3">WITHOUT AUTOMATION</div>
                  <div className="space-y-3">
                    <div className="bg-white rounded-lg p-3 border border-gray-200">
                      <div className="flex items-center gap-2 mb-1">
                        <Clock className="w-4 h-4 text-gray-400" />
                        <span className="text-sm font-medium text-gray-900">Days 1-5</span>
                      </div>
                      <p className="text-sm text-gray-600">Manually review pages, check meta data, note issues</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-gray-200">
                      <div className="flex items-center gap-2 mb-1">
                        <Clock className="w-4 h-4 text-gray-400" />
                        <span className="text-sm font-medium text-gray-900">Days 6-8</span>
                      </div>
                      <p className="text-sm text-gray-600">Compile findings into a report, prioritize manually</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-gray-200">
                      <div className="flex items-center gap-2 mb-1">
                        <Clock className="w-4 h-4 text-gray-400" />
                        <span className="text-sm font-medium text-gray-900">Days 9-10</span>
                      </div>
                      <p className="text-sm text-gray-600">Distribute to team, create action items</p>
                    </div>
                  </div>
                </div>

                <div className="flex justify-center">
                  <div className="w-full border-t-2 border-dashed border-gray-300"></div>
                </div>

                <div>
                  <div className="text-sm font-medium text-gray-500 mb-3">WITH AI WEBSCRAPER</div>
                  <div className="space-y-3">
                    <div className="bg-white rounded-lg p-3 border border-green-200">
                      <div className="flex items-center gap-2 mb-1">
                        <Zap className="w-4 h-4 text-green-600" />
                        <span className="text-sm font-medium text-gray-900">Minutes</span>
                      </div>
                      <p className="text-sm text-gray-600">Crawl the site and detect issues automatically</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-green-200">
                      <div className="flex items-center gap-2 mb-1">
                        <Zap className="w-4 h-4 text-green-600" />
                        <span className="text-sm font-medium text-gray-900">Same Day</span>
                      </div>
                      <p className="text-sm text-gray-600">Generate AI report with prioritized, actionable fixes</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-green-200">
                      <div className="flex items-center gap-2 mb-1">
                        <Zap className="w-4 h-4 text-green-600" />
                        <span className="text-sm font-medium text-gray-900">Next Day</span>
                      </div>
                      <p className="text-sm text-gray-600">Team starts fixing — highest-impact items first</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Use Case 4: Web Development Agency */}
      <section className="py-20 bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-orange-100 text-orange-700 rounded-full text-sm font-medium mb-4">
              Web Development Agency
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
              Turn Website Launches Into Ongoing Relationships
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Most dev agencies build a site and move on. The opportunity is offering ongoing site
              health monitoring as a value-added service — turning one-time projects into recurring revenue.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mb-4">
                <Users className="w-6 h-6 text-orange-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">The Service Model</h3>
              <p className="text-gray-600 mb-4">
                After launching a client's site, offer monthly health reports as a premium add-on.
                Most clients value the peace of mind — especially if their website drives leads or sales.
              </p>
              <div className="text-sm text-orange-600 font-medium">
                Low effort, high perceived value
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mb-4">
                <Target className="w-6 h-6 text-orange-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">What You Deliver</h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                  Monthly site health reports
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                  SEO issue monitoring
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                  Broken link detection
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                  Accessibility compliance checks
                </li>
              </ul>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mb-4">
                <DollarSign className="w-6 h-6 text-orange-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">The Business Case</h3>
              <p className="text-gray-600 mb-4">
                AI WebScraper does the heavy lifting. Your team reviews the output and presents it
                to the client. Minimal time investment with strong margins — the kind of service
                that scales.
              </p>
              <div className="text-sm text-orange-600 font-medium">
                Recurring revenue from existing relationships
              </div>
            </div>
          </div>

          <div className="mt-12 bg-gradient-to-br from-orange-50 to-yellow-50 rounded-2xl p-8 border border-orange-200">
            <div className="text-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Why This Works</h3>
              <p className="text-gray-600">Recurring services benefit both you and your clients</p>
            </div>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-lg font-bold text-orange-600 mb-2">For Your Agency</div>
                <p className="text-sm text-gray-600">
                  Predictable monthly revenue, deeper client relationships, and a reason to stay in touch
                  after launch day.
                </p>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-orange-600 mb-2">For Your Clients</div>
                <p className="text-sm text-gray-600">
                  Peace of mind that their site stays healthy. Issues caught before they become
                  problems. Expert guidance on tap.
                </p>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-orange-600 mb-2">For Retention</div>
                <p className="text-sm text-gray-600">
                  Clients who get monthly reports feel cared for. When they need their next project built,
                  you're already the trusted partner.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-br from-secondary-600 to-primary-600 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-6">
            See What Your Site Audit Looks Like
          </h2>
          <p className="text-xl text-secondary-100 mb-8">
            Paste your URL and get a consultant-grade audit in minutes. Free to start.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/signup"
              className="px-8 py-4 bg-white text-secondary-600 rounded-lg font-semibold text-lg hover:bg-gray-100 transition-all shadow-lg"
            >
              Start Free Audit
            </Link>
            <Link
              to="/about"
              className="px-8 py-4 bg-secondary-700 hover:bg-secondary-800 text-white rounded-lg font-semibold text-lg border-2 border-secondary-500 transition-all"
            >
              Learn More
            </Link>
          </div>
          <p className="mt-6 text-sm text-secondary-200">
            Free tier includes 3 full site audits — no credit card required
          </p>
        </div>
      </section>
    </div>
  );
};

export default UseCasesPage;
