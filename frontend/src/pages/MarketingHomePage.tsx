import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  Sparkles, 
  Target, 
  TrendingUp, 
  Shield, 
  Zap, 
  CheckCircle, 
  ArrowRight,
  BarChart3,
  Brain,
  Image as ImageIcon,
  FileSearch,
  Globe,
  Lock
} from 'lucide-react';

const MarketingHomePage: React.FC = () => {
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
      <section className="relative overflow-hidden bg-gradient-to-br from-secondary-50 via-white to-primary-50 pt-20 pb-32">
        <div className="absolute inset-0 bg-grid-slate-100 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))] -z-10" />
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-secondary-100 text-secondary-700 rounded-full text-sm font-medium mb-8">
              <Sparkles className="w-4 h-4" />
              AI-Powered Web Intelligence Platform
            </div>
            
            <h1 className="text-5xl md:text-7xl font-bold text-gray-900 mb-6 leading-tight">
              Transform Websites Into
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-secondary-600 to-primary-600">
                Actionable Intelligence
              </span>
            </h1>
            
            <p className="text-xl md:text-2xl text-gray-600 max-w-3xl mx-auto mb-12 leading-relaxed">
              Go beyond basic web scraping. Get AI-powered content analysis, SEO recommendations, 
              and accessibility insights that drive real business results.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <button
                onClick={handleGetStarted}
                className="group px-8 py-4 bg-secondary-600 hover:bg-secondary-700 text-white rounded-lg font-semibold text-lg shadow-lg hover:shadow-xl transition-all flex items-center gap-2"
              >
                {user ? 'Go to Dashboard' : 'Start Free Trial'}
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>
              <Link
                to="/quick-start"
                className="px-8 py-4 bg-white hover:bg-gray-50 text-gray-900 rounded-lg font-semibold text-lg border-2 border-gray-200 hover:border-gray-300 transition-all"
              >
                View Documentation
              </Link>
            </div>
            
            <p className="mt-6 text-sm text-gray-500">
              No credit card required • 14-day free trial • Cancel anytime
            </p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mt-20 max-w-4xl mx-auto">
            <div className="text-center">
              <div className="text-4xl font-bold text-gray-900">14</div>
              <div className="text-sm text-gray-600 mt-1">AI Analysis Tasks</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-gray-900">$0.001</div>
              <div className="text-sm text-gray-600 mt-1">Cost Per Page</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-gray-900">90%</div>
              <div className="text-sm text-gray-600 mt-1">Accuracy Rate</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-gray-900">24/7</div>
              <div className="text-sm text-gray-600 mt-1">Automated Crawling</div>
            </div>
          </div>
        </div>
      </section>

      {/* Problem Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold text-gray-900 mb-6">
              Stop Wasting Time on Manual Website Audits
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Traditional web scraping tools just dump data. You need AI-powered insights that tell you exactly what to fix.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="p-8 bg-red-50 border border-red-100 rounded-xl hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-red-500 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Manual Analysis Takes Days</h3>
              <p className="text-gray-600">
                Reviewing 100 pages manually? That's 40+ hours of tedious work checking SEO, content quality, and accessibility—one page at a time.
              </p>
            </div>

            <div className="p-8 bg-red-50 border border-red-100 rounded-xl hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-red-500 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Expensive Agency Fees</h3>
              <p className="text-gray-600">
                Agencies charge $2,000-5,000/month for basic audits. You're paying for manual labor when AI can do it better, faster, and cheaper.
              </p>
            </div>

            <div className="p-8 bg-red-50 border border-red-100 rounded-xl hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-red-500 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Data Without Insights</h3>
              <p className="text-gray-600">
                Basic scrapers dump spreadsheets of URLs and metrics. You still have to analyze everything and figure out what actually needs fixing.
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
              AI-Powered Features That Drive Results
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Every feature designed to save time, reduce costs, and deliver actionable insights.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="group p-8 bg-white rounded-xl border border-gray-200 hover:border-secondary-300 hover:shadow-lg transition-all">
              <div className="w-12 h-12 bg-secondary-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-secondary-200 transition-colors">
                <Brain className="w-6 h-6 text-secondary-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">AI Content Analysis</h3>
              <p className="text-gray-600 mb-4">
                GPT-4 powered summaries, categorization, and topic extraction for every page. Understand your content at scale.
              </p>
              <div className="text-sm text-secondary-600 font-medium">$0.0005 per page</div>
            </div>

            {/* Feature 2 */}
            <div className="group p-8 bg-white rounded-xl border border-gray-200 hover:border-secondary-300 hover:shadow-lg transition-all">
              <div className="w-12 h-12 bg-secondary-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-secondary-200 transition-colors">
                <TrendingUp className="w-6 h-6 text-secondary-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">SEO Recommendations</h3>
              <p className="text-gray-600 mb-4">
                Get specific, actionable SEO improvements for meta descriptions, titles, keywords, and content structure.
              </p>
              <div className="text-sm text-secondary-600 font-medium">AI-generated insights</div>
            </div>

            {/* Feature 3 */}
            <div className="group p-8 bg-white rounded-xl border border-gray-200 hover:border-secondary-300 hover:shadow-lg transition-all">
              <div className="w-12 h-12 bg-secondary-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-secondary-200 transition-colors">
                <BarChart3 className="w-6 h-6 text-secondary-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Content Quality Scoring</h3>
              <p className="text-gray-600 mb-4">
                Automated scoring for clarity, relevance, engagement, and structure with specific improvement recommendations.
              </p>
              <div className="text-sm text-secondary-600 font-medium">0-100 quality score</div>
            </div>

            {/* Feature 4 */}
            <div className="group p-8 bg-white rounded-xl border border-gray-200 hover:border-secondary-300 hover:shadow-lg transition-all">
              <div className="w-12 h-12 bg-secondary-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-secondary-200 transition-colors">
                <ImageIcon className="w-6 h-6 text-secondary-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Image Accessibility</h3>
              <p className="text-gray-600 mb-4">
                AI-generated alt text for WCAG compliance. Automatically identify decorative vs. content images.
              </p>
              <div className="text-sm text-secondary-600 font-medium">90% confidence rate</div>
            </div>

            {/* Feature 5 */}
            <div className="group p-8 bg-white rounded-xl border border-gray-200 hover:border-secondary-300 hover:shadow-lg transition-all">
              <div className="w-12 h-12 bg-secondary-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-secondary-200 transition-colors">
                <FileSearch className="w-6 h-6 text-secondary-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Semantic Search</h3>
              <p className="text-gray-600 mb-4">
                Vector embeddings enable finding similar content across your site. Identify duplicate or related pages instantly.
              </p>
              <div className="text-sm text-secondary-600 font-medium">Powered by embeddings</div>
            </div>

            {/* Feature 6 */}
            <div className="group p-8 bg-white rounded-xl border border-gray-200 hover:border-secondary-300 hover:shadow-lg transition-all">
              <div className="w-12 h-12 bg-secondary-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-secondary-200 transition-colors">
                <Shield className="w-6 h-6 text-secondary-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Cost Transparency</h3>
              <p className="text-gray-600 mb-4">
                Track every API call and cost. Set budget limits per crawl. No surprise bills, complete visibility.
              </p>
              <div className="text-sm text-secondary-600 font-medium">Real-time tracking</div>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div>
              <h2 className="text-3xl md:text-5xl font-bold text-gray-900 mb-6">
                Built for SEO Agencies, Content Teams, and Enterprises
              </h2>
              <p className="text-xl text-gray-600 mb-8">
                Whether you're auditing client sites, maintaining content quality, or ensuring accessibility compliance, 
                our platform delivers the insights you need.
              </p>

              <div className="space-y-6">
                <div className="flex gap-4">
                  <div className="flex-shrink-0">
                    <CheckCircle className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">Save 20+ Hours Per Audit</h3>
                    <p className="text-gray-600">Automate content analysis, SEO checks, and accessibility reviews that used to take days.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="flex-shrink-0">
                    <CheckCircle className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">Reduce Costs by 80%</h3>
                    <p className="text-gray-600">Pay pennies per page instead of thousands per month for agency audits.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="flex-shrink-0">
                    <CheckCircle className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">Scale to Thousands of Pages</h3>
                    <p className="text-gray-600">Analyze entire websites with hundreds or thousands of pages in minutes, not weeks.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="flex-shrink-0">
                    <CheckCircle className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">Actionable, Not Just Data</h3>
                    <p className="text-gray-600">Get specific recommendations you can implement immediately, not just raw metrics.</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-secondary-50 to-primary-50 rounded-2xl p-8 border border-gray-200">
              <div className="bg-white rounded-xl p-6 shadow-lg mb-6">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-sm font-medium text-gray-500">Content Quality</span>
                  <span className="text-2xl font-bold text-green-600">87/100</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-green-600 h-2 rounded-full" style={{width: '87%'}}></div>
                </div>
              </div>

              <div className="bg-white rounded-xl p-6 shadow-lg mb-6">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-sm font-medium text-gray-500">SEO Score</span>
                  <span className="text-2xl font-bold text-blue-600">92/100</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{width: '92%'}}></div>
                </div>
              </div>

              <div className="bg-white rounded-xl p-6 shadow-lg">
                <div className="text-sm font-medium text-gray-500 mb-3">AI Recommendations</div>
                <ul className="space-y-2">
                  <li className="flex items-start gap-2 text-sm text-gray-700">
                    <Zap className="w-4 h-4 text-yellow-500 flex-shrink-0 mt-0.5" />
                    <span>Add target keywords to H2 headings</span>
                  </li>
                  <li className="flex items-start gap-2 text-sm text-gray-700">
                    <Zap className="w-4 h-4 text-yellow-500 flex-shrink-0 mt-0.5" />
                    <span>Optimize meta description length</span>
                  </li>
                  <li className="flex items-start gap-2 text-sm text-gray-700">
                    <Zap className="w-4 h-4 text-yellow-500 flex-shrink-0 mt-0.5" />
                    <span>Add alt text to 12 images</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold text-gray-900 mb-6">
              Trusted by Industry Leaders
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              From SEO agencies to enterprise content teams, see how professionals use our platform.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white p-8 rounded-xl border border-gray-200">
              <Target className="w-10 h-10 text-secondary-600 mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-3">SEO Agencies</h3>
              <p className="text-gray-600 mb-4">
                Audit client websites faster, deliver comprehensive reports, and identify optimization opportunities automatically.
              </p>
              <div className="text-sm font-medium text-secondary-600">$500-2000/mo saved per client</div>
            </div>

            <div className="bg-white p-8 rounded-xl border border-gray-200">
              <Globe className="w-10 h-10 text-secondary-600 mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Content Teams</h3>
              <p className="text-gray-600 mb-4">
                Maintain content quality at scale, ensure brand voice consistency, and identify content gaps across your site.
              </p>
              <div className="text-sm font-medium text-secondary-600">20+ hours saved per audit</div>
            </div>

            <div className="bg-white p-8 rounded-xl border border-gray-200">
              <Lock className="w-10 h-10 text-secondary-600 mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Accessibility Consultants</h3>
              <p className="text-gray-600 mb-4">
                Automate WCAG compliance checks, generate alt text for images, and identify accessibility issues instantly.
              </p>
              <div className="text-sm font-medium text-secondary-600">90% faster compliance audits</div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-br from-secondary-600 to-primary-600 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Ready to Transform Your Website Analysis?
          </h2>
          <p className="text-xl mb-8 text-secondary-100">
            Join hundreds of professionals who've automated their content audits with AI.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={handleGetStarted}
              className="px-8 py-4 bg-white text-secondary-600 rounded-lg font-semibold text-lg hover:bg-gray-100 transition-all shadow-lg"
            >
              Start Free Trial
            </button>
            <Link
              to="/quick-start"
              className="px-8 py-4 bg-secondary-700 hover:bg-secondary-800 text-white rounded-lg font-semibold text-lg border-2 border-secondary-500 transition-all"
            >
              View Documentation
            </Link>
          </div>
          <p className="mt-6 text-sm text-secondary-100">
            14-day free trial • No credit card required • Cancel anytime
          </p>
        </div>
      </section>
    </div>
  );
};

export default MarketingHomePage;
