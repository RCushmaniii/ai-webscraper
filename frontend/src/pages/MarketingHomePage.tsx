import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  Sparkles,
  Target,
  TrendingUp,
  Zap,
  CheckCircle,
  ArrowRight,
  BarChart3,
  Brain,
  Search,
  FileText,
  Layers,
  Clock,
  DollarSign,
  Users,
  Briefcase,
  Rocket
} from 'lucide-react';
import { usePageTitle } from '../hooks/usePageTitle';

const MarketingHomePage: React.FC = () => {
  usePageTitle('AI-Powered Site Audits', 'Crawl your website, detect SEO and accessibility issues, and get AI-powered recommendations you can act on immediately. Free audit available.');

  const { user } = useAuth();
  const navigate = useNavigate();

  const handleGetStarted = () => {
    if (user) {
      navigate('/dashboard');
    } else {
      navigate('/signup');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-secondary-50 via-white to-primary-50 pt-12 pb-16 sm:pt-20 sm:pb-32">
        <div className="absolute inset-0 bg-grid-slate-100 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))] -z-10" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-secondary-100 text-secondary-700 rounded-full text-sm font-medium mb-8">
              <Sparkles className="w-4 h-4" />
              AI-Powered Site Consultant
            </div>

            <h1 className="text-3xl sm:text-5xl md:text-7xl font-bold text-gray-900 mb-6 leading-tight">
              Other Tools Tell You What's Broken.
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-secondary-600 to-primary-600">
                I Tell You How to Fix It.
              </span>
            </h1>

            <p className="text-lg sm:text-xl md:text-2xl text-gray-600 max-w-3xl mx-auto mb-6 leading-relaxed">
              Most audit tools tell you what's wrong. I tell you <strong>what to do about it</strong>,{' '}
              <strong>in what order</strong>, and <strong>how long it'll take</strong> — then show you how
              you stack up against your competition.
            </p>

            <p className="text-lg text-gray-500 max-w-2xl mx-auto mb-12">
              It's not a crawler with an AI bolt-on. It's an AI consultant with a crawler built in.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <button
                onClick={handleGetStarted}
                className="group px-8 py-4 bg-secondary-600 hover:bg-secondary-700 text-white rounded-lg font-semibold text-lg shadow-lg hover:shadow-xl transition-all flex items-center gap-2"
              >
                {user ? 'Go to Dashboard' : 'Start Free Audit'}
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>
              <Link
                to="/quick-start"
                className="px-8 py-4 bg-white hover:bg-gray-50 text-gray-900 rounded-lg font-semibold text-lg border-2 border-gray-200 hover:border-gray-300 transition-all"
              >
                See How It Works
              </Link>
            </div>

            <p className="mt-6 text-sm text-gray-500">
              Free to start — no credit card required
            </p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mt-20 max-w-4xl mx-auto">
            <div className="text-center">
              <div className="text-2xl sm:text-4xl font-bold text-gray-900">3 min</div>
              <div className="text-xs sm:text-sm text-gray-600 mt-1">Full Site Audit</div>
            </div>
            <div className="text-center">
              <div className="text-2xl sm:text-4xl font-bold text-gray-900">50+</div>
              <div className="text-xs sm:text-sm text-gray-600 mt-1">Issues Detected</div>
            </div>
            <div className="text-center">
              <div className="text-2xl sm:text-4xl font-bold text-gray-900">$$$</div>
              <div className="text-xs sm:text-sm text-gray-600 mt-1">vs. Consultant Fees</div>
            </div>
            <div className="text-center">
              <div className="text-2xl sm:text-4xl font-bold text-gray-900">5x</div>
              <div className="text-xs sm:text-sm text-gray-600 mt-1">Faster Than Manual</div>
            </div>
          </div>
        </div>
      </section>

      {/* Problem Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold text-gray-900 mb-6">
              Site Audit Tools Give You Data.<br />You Need Answers.
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              You've tried the crawlers. They dump 500 rows into a spreadsheet and leave you to figure out what matters.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="p-8 bg-red-50 border border-red-100 rounded-xl hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-red-500 rounded-lg flex items-center justify-center mb-4">
                <Clock className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">"Fix Your Broken Links"</h3>
              <p className="text-gray-600">
                Great — but which ones matter? A 404 on your pricing page is urgent. A broken link to an old blog post? Not so much.
                Most tools treat them the same.
              </p>
            </div>

            <div className="p-8 bg-red-50 border border-red-100 rounded-xl hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-red-500 rounded-lg flex items-center justify-center mb-4">
                <DollarSign className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">"Hire a Consultant"</h3>
              <p className="text-gray-600">
                A proper site audit can cost thousands. You get a PDF weeks later. Many recommendations are generic.
                The rest you can't implement without paying even more.
              </p>
            </div>

            <div className="p-8 bg-red-50 border border-red-100 rounded-xl hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-red-500 rounded-lg flex items-center justify-center mb-4">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">"Export to CSV"</h3>
              <p className="text-gray-600">
                A spreadsheet of URLs, status codes, and meta lengths isn't a strategy. You need someone to tell you
                what to fix, why, and in what order. That's what this tool does.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold text-gray-900 mb-6">
              What Your Audit Actually Includes
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Not just metrics. A prioritized action plan with specific fixes you can implement today.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="group p-8 bg-white rounded-xl border border-gray-200 hover:border-secondary-300 hover:shadow-lg transition-all">
              <div className="w-12 h-12 bg-secondary-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-secondary-200 transition-colors">
                <Search className="w-6 h-6 text-secondary-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Intelligent Crawling</h3>
              <p className="text-gray-600 mb-4">
                Maps every page, link, image, and heading on your site. Auto-detects JavaScript-rendered pages
                and re-fetches them via cloud rendering. No false positives.
              </p>
              <div className="text-sm text-secondary-600 font-medium">Configurable depth + page limits</div>
            </div>

            {/* Feature 2 */}
            <div className="group p-8 bg-white rounded-xl border border-gray-200 hover:border-secondary-300 hover:shadow-lg transition-all">
              <div className="w-12 h-12 bg-secondary-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-secondary-200 transition-colors">
                <Layers className="w-6 h-6 text-secondary-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Page-by-Page Audit</h3>
              <p className="text-gray-600 mb-4">
                Every page gets a detailed audit card: SEO metadata, content depth, image accessibility,
                link health, response times, and heading structure — all color-coded by severity.
              </p>
              <div className="text-sm text-secondary-600 font-medium">Specific issues per page</div>
            </div>

            {/* Feature 3 */}
            <div className="group p-8 bg-white rounded-xl border border-gray-200 hover:border-secondary-300 hover:shadow-lg transition-all">
              <div className="w-12 h-12 bg-secondary-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-secondary-200 transition-colors">
                <Brain className="w-6 h-6 text-secondary-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">AI Consultant Reports</h3>
              <p className="text-gray-600 mb-4">
                The kind of report you'd expect from a seasoned strategist — generated in minutes. Business-impact prioritization,
                specific fixes, and effort estimates for every recommendation.
              </p>
              <div className="text-sm text-secondary-600 font-medium">AI-generated analysis</div>
            </div>

            {/* Feature 4 */}
            <div className="group p-8 bg-white rounded-xl border border-gray-200 hover:border-secondary-300 hover:shadow-lg transition-all">
              <div className="w-12 h-12 bg-secondary-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-secondary-200 transition-colors">
                <TrendingUp className="w-6 h-6 text-secondary-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Brand Voice Analysis</h3>
              <p className="text-gray-600 mb-4">
                Does your homepage sound corporate while your blog sounds casual? The AI analyzes tone
                consistency across your page titles, headings, and meta descriptions.
              </p>
              <div className="text-sm text-secondary-600 font-medium">No other crawler does this</div>
            </div>

            {/* Feature 5 */}
            <div className="group p-8 bg-white rounded-xl border border-gray-200 hover:border-secondary-300 hover:shadow-lg transition-all">
              <div className="w-12 h-12 bg-secondary-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-secondary-200 transition-colors">
                <Target className="w-6 h-6 text-secondary-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Competitive Comparison</h3>
              <p className="text-gray-600 mb-4">
                Crawl your site and a competitor's. Compare structural patterns, content depth, and SEO signals
                to understand where you stand and where to improve.
              </p>
              <div className="text-sm text-secondary-600 font-medium">Premium feature</div>
            </div>

            {/* Feature 6 */}
            <div className="group p-8 bg-white rounded-xl border border-gray-200 hover:border-secondary-300 hover:shadow-lg transition-all">
              <div className="w-12 h-12 bg-secondary-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-secondary-200 transition-colors">
                <BarChart3 className="w-6 h-6 text-secondary-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Exportable Deliverables</h3>
              <p className="text-gray-600 mb-4">
                CSV for developers, structured reports for project managers, executive summaries for
                stakeholders. Hand it off and get to work.
              </p>
              <div className="text-sm text-secondary-600 font-medium">Client-ready output</div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold text-gray-900 mb-6">
              How It Works
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Paste a URL. Get a consultant-grade report. Three steps, three minutes.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-12 max-w-5xl mx-auto">
            <div className="text-center">
              <div className="w-16 h-16 bg-secondary-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-2xl font-bold text-secondary-600">1</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Paste Your URL</h3>
              <p className="text-gray-600">
                Enter any website URL. Configure depth, page limits, and crawl settings — or just use the defaults.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-secondary-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-2xl font-bold text-secondary-600">2</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">AI Analyzes Everything</h3>
              <p className="text-gray-600">
                The crawler maps your site. The issue detector flags problems. The AI prioritizes fixes by business impact.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-secondary-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-2xl font-bold text-secondary-600">3</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Get Your Action Plan</h3>
              <p className="text-gray-600">
                A prioritized report with specific fixes, effort estimates, and exportable deliverables. Hand it to your team and go.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Who It's For */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold text-gray-900 mb-6">
              Built For People Who Ship
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Whether you're managing clients, running a business, or building your own thing — this tool pays for itself on the first audit.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white p-8 rounded-xl border border-gray-200 hover:shadow-lg transition-shadow">
              <Users className="w-10 h-10 text-secondary-600 mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Marketing Agencies</h3>
              <p className="text-gray-600 mb-4">
                Audit 10 client sites per day instead of 2. Generate client-ready reports in minutes.
                Use competitive comparison as an upsell that closes deals.
              </p>
              <ul className="space-y-2">
                <li className="flex items-start gap-2 text-sm text-gray-700">
                  <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                  <span>Client-ready deliverables, auto-generated</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-gray-700">
                  <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                  <span>5x audit throughput per analyst</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-gray-700">
                  <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                  <span>Competitive comparison for upsells</span>
                </li>
              </ul>
            </div>

            <div className="bg-white p-8 rounded-xl border border-gray-200 hover:shadow-lg transition-shadow">
              <Briefcase className="w-10 h-10 text-secondary-600 mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Small Businesses</h3>
              <p className="text-gray-600 mb-4">
                No SEO team? No problem. Get plain-English recommendations with effort estimates. Know exactly
                what's a 5-minute fix vs. what needs a developer.
              </p>
              <ul className="space-y-2">
                <li className="flex items-start gap-2 text-sm text-gray-700">
                  <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                  <span>Plain English, no jargon</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-gray-700">
                  <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                  <span>Effort estimates on every fix</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-gray-700">
                  <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                  <span>Fraction of consultant cost</span>
                </li>
              </ul>
            </div>

            <div className="bg-white p-8 rounded-xl border border-gray-200 hover:shadow-lg transition-shadow">
              <Rocket className="w-10 h-10 text-secondary-600 mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Founders</h3>
              <p className="text-gray-600 mb-4">
                You built the site. It looks fine. But is it actually working for you? Paste your URL,
                get a complete audit, and see how you compare to competitors.
              </p>
              <ul className="space-y-2">
                <li className="flex items-start gap-2 text-sm text-gray-700">
                  <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                  <span>One-click site audit</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-gray-700">
                  <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                  <span>AI prioritizes what matters most</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-gray-700">
                  <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                  <span>Competitive intelligence built in</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Differentiator Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div>
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
                What Traditional Crawlers Can't Do
              </h2>
              <p className="text-xl text-gray-600 mb-8">
                Traditional crawlers tell you your meta description is too long.
                I tell you what to change it to.
              </p>

              <div className="space-y-6">
                <div className="flex gap-4">
                  <div className="flex-shrink-0">
                    <Zap className="w-6 h-6 text-secondary-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">Business Impact Prioritization</h3>
                    <p className="text-gray-600">A 404 on your pricing page isn't the same as a missing alt tag on a decorative image. The AI knows the difference and ranks accordingly.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="flex-shrink-0">
                    <Zap className="w-6 h-6 text-secondary-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">Copy-Paste Fixes</h3>
                    <p className="text-gray-600">"Change your meta description on /services from [current] to [suggested]." Hand this to your developer. Done.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="flex-shrink-0">
                    <Zap className="w-6 h-6 text-secondary-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">Brand Voice Consistency</h3>
                    <p className="text-gray-600">No other crawl tool checks whether your site speaks with a consistent voice. I catch mismatches that erode your brand.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="flex-shrink-0">
                    <Zap className="w-6 h-6 text-secondary-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">Effort Estimates</h3>
                    <p className="text-gray-600">Every recommendation tagged: "Quick fix (5 min)" or "Needs developer (2 hrs)." Plan your sprint, not just your wishlist.</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-secondary-50 to-primary-50 rounded-2xl p-8 border border-gray-200">
              <div className="bg-white rounded-xl p-6 shadow-lg mb-6">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-sm font-medium text-gray-500">Site Health Score</span>
                  <span className="text-2xl font-bold text-green-600">84/100</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-green-600 h-2 rounded-full" style={{width: '84%'}}></div>
                </div>
              </div>

              <div className="bg-white rounded-xl p-6 shadow-lg mb-6">
                <div className="text-sm font-medium text-gray-500 mb-3">Top Priority Fixes</div>
                <ul className="space-y-3">
                  <li className="flex items-start gap-3 text-sm">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700 flex-shrink-0 mt-0.5">Critical</span>
                    <span className="text-gray-700">Fix 404 at /pricing — high-traffic conversion page</span>
                  </li>
                  <li className="flex items-start gap-3 text-sm">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-700 flex-shrink-0 mt-0.5">Medium</span>
                    <span className="text-gray-700">Meta description on /services is 167 chars (7 over limit)</span>
                  </li>
                  <li className="flex items-start gap-3 text-sm">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700 flex-shrink-0 mt-0.5">Quick Win</span>
                    <span className="text-gray-700">Add alt text to hero image on homepage</span>
                  </li>
                </ul>
              </div>

              <div className="bg-white rounded-xl p-6 shadow-lg">
                <div className="text-sm font-medium text-gray-500 mb-3">Effort Breakdown</div>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-green-600">4</div>
                    <div className="text-xs text-gray-500">Quick fixes</div>
                    <div className="text-xs text-gray-400">~20 min total</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-yellow-600">2</div>
                    <div className="text-xs text-gray-500">Dev tasks</div>
                    <div className="text-xs text-gray-400">~3 hrs total</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-blue-600">1</div>
                    <div className="text-xs text-gray-500">Strategic</div>
                    <div className="text-xs text-gray-400">Ongoing</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-br from-secondary-600 to-primary-600 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-6">
            Stop Guessing. Start Fixing.
          </h2>
          <p className="text-xl mb-4 text-secondary-100">
            Paste your URL. Get a consultant-grade audit in 3 minutes.
          </p>
          <p className="text-lg mb-8 text-secondary-200">
            See exactly what's wrong, what to fix first, and how long each fix takes.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={handleGetStarted}
              className="px-8 py-4 bg-white text-secondary-600 rounded-lg font-semibold text-lg hover:bg-gray-100 transition-all shadow-lg"
            >
              {user ? 'Go to Dashboard' : 'Start Your Free Audit'}
            </button>
          </div>
          <p className="mt-6 text-sm text-secondary-200">
            Free tier includes 3 full site audits — no credit card needed
          </p>
        </div>
      </section>
    </div>
  );
};

export default MarketingHomePage;
