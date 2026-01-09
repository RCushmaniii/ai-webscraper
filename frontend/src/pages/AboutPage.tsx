import React from 'react';
import { Sparkles, Zap, Code, Brain, Layers, TrendingUp, Users, Globe, Rocket } from 'lucide-react';

const AboutPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-secondary-50 via-white to-primary-50 py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-secondary-100 text-secondary-700 rounded-full text-sm font-medium mb-6">
              <Sparkles className="w-4 h-4" />
              About AI WebScraper
            </div>
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
              What Wasn't Possible a Year Ago
            </h1>
            <p className="text-xl text-gray-600 leading-relaxed">
              AI WebScraper represents the convergence of modern technologies—Python, React, and Large Language Models—creating 
              something fundamentally new: web intelligence that understands content like a human, but scales like a machine.
            </p>
          </div>
        </div>
      </section>

      {/* The Problem Section */}
      <section className="py-16 bg-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-8">The Problem We're Solving</h2>
          
          <div className="space-y-6">
            <div className="border-l-4 border-red-500 pl-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Traditional Web Scraping is Broken</h3>
              <p className="text-gray-700 leading-relaxed">
                For decades, web scraping meant extracting raw HTML and hoping you could make sense of it. You'd get URLs, 
                titles, and text—but no understanding. No insights. No actionable recommendations. Just data dumps that 
                required hours of manual analysis.
              </p>
            </div>

            <div className="border-l-4 border-red-500 pl-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">SEO Audits Cost Thousands</h3>
              <p className="text-gray-700 leading-relaxed">
                Agencies charge $2,000-5,000 per month for what amounts to manual labor: someone clicking through your site, 
                checking meta tags, reading content, and writing up recommendations. It's slow, expensive, and doesn't scale.
              </p>
            </div>

            <div className="border-l-4 border-red-500 pl-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Accessibility Compliance is Manual</h3>
              <p className="text-gray-700 leading-relaxed">
                WCAG compliance requires alt text for every image. For a 500-page site with 2,000 images, that's weeks of work. 
                Most companies simply don't do it, risking legal issues and excluding users with disabilities.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* The Solution Section */}
      <section className="py-16 bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-8">What's Now Possible</h2>
          
          <div className="space-y-8">
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-secondary-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Brain className="w-6 h-6 text-secondary-600" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">AI That Understands Content</h3>
                  <p className="text-gray-700 leading-relaxed">
                    Advanced language models don't just extract text—they read and comprehend it. They can summarize a 2,000-word article into 
                    3 sentences, identify the target audience, extract key topics, and categorize the page type. This level of 
                    understanding was impossible with traditional NLP.
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-secondary-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Zap className="w-6 h-6 text-secondary-600" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">Actionable Recommendations, Not Raw Data</h3>
                  <p className="text-gray-700 leading-relaxed">
                    Instead of "here's your meta description," you get "your meta description is 180 characters—trim it to 155 
                    and include your target keyword 'enterprise software.'" Specific, actionable, ready to implement.
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-secondary-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <TrendingUp className="w-6 h-6 text-secondary-600" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">Scale That Was Impossible Before</h3>
                  <p className="text-gray-700 leading-relaxed">
                    Analyze 1,000 pages in minutes, not weeks. Generate alt text for 5,000 images in an hour, not months. 
                    Get content quality scores for an entire website before lunch. The combination of automated crawling and 
                    AI analysis makes this possible.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Who Benefits Section */}
      <section className="py-16 bg-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3 mb-8">
            <Users className="w-8 h-8 text-secondary-600" />
            <h2 className="text-3xl font-bold text-gray-900">Who This Serves</h2>
          </div>

          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h3 className="text-xl font-semibold text-gray-900 mb-3">SEO Agencies & Consultants</h3>
              <p className="text-gray-700 leading-relaxed mb-3">
                Deliver comprehensive site audits in hours instead of days. Provide clients with AI-powered insights 
                they can't get anywhere else. Scale your services without hiring more analysts.
              </p>
              <div className="text-sm text-secondary-600 font-medium">
                Save 20+ hours per audit • Serve more clients • Deliver better insights
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Content Teams & Marketers</h3>
              <p className="text-gray-700 leading-relaxed mb-3">
                Maintain content quality across hundreds or thousands of pages. Identify gaps, inconsistencies, and 
                opportunities automatically. Get specific recommendations for improvement.
              </p>
              <div className="text-sm text-secondary-600 font-medium">
                Quality scoring • Brand voice consistency • Content gap analysis
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Accessibility Professionals</h3>
              <p className="text-gray-700 leading-relaxed mb-3">
                Automate WCAG compliance checks. Generate contextual alt text for thousands of images. Identify 
                accessibility issues at scale and provide specific remediation steps.
              </p>
              <div className="text-sm text-secondary-600 font-medium">
                90% faster audits • AI-generated alt text • WCAG compliance tracking
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Enterprise Teams</h3>
              <p className="text-gray-700 leading-relaxed mb-3">
                Monitor content quality across multiple properties. Track competitor content strategies. Ensure 
                brand consistency and SEO best practices at scale.
              </p>
              <div className="text-sm text-secondary-600 font-medium">
                Multi-site monitoring • Competitive analysis • Executive reporting
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Web Development Agencies</h3>
              <p className="text-gray-700 leading-relaxed mb-3">
                Offer value-added services to clients beyond just building websites. Provide ongoing content audits, 
                SEO monitoring, and accessibility compliance as part of your service packages.
              </p>
              <div className="text-sm text-secondary-600 font-medium">
                Recurring revenue • Client retention • Premium service offerings
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Technology Stack Section */}
      <section className="py-16 bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3 mb-8">
            <Code className="w-8 h-8 text-secondary-600" />
            <h2 className="text-3xl font-bold text-gray-900">The Technology Behind It</h2>
          </div>

          <p className="text-gray-700 leading-relaxed mb-8">
            AI WebScraper is built on a modern stack that combines the best of web development, backend processing, 
            and artificial intelligence. Each piece is essential to making this work at scale.
          </p>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
              <div className="flex items-center gap-2 mb-3">
                <Layers className="w-5 h-5 text-secondary-600" />
                <h3 className="text-lg font-semibold text-gray-900">React Frontend</h3>
              </div>
              <p className="text-gray-700 text-sm leading-relaxed">
                Modern, responsive UI built with React and Tailwind CSS. Real-time updates, intuitive dashboards, 
                and a polished user experience that makes complex data accessible.
              </p>
            </div>

            <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
              <div className="flex items-center gap-2 mb-3">
                <Code className="w-5 h-5 text-secondary-600" />
                <h3 className="text-lg font-semibold text-gray-900">Python Backend</h3>
              </div>
              <p className="text-gray-700 text-sm leading-relaxed">
                FastAPI powers the backend with async processing, type safety, and automatic API documentation. 
                Handles crawling, data processing, and orchestrates AI analysis at scale.
              </p>
            </div>

            <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
              <div className="flex items-center gap-2 mb-3">
                <Brain className="w-5 h-5 text-secondary-600" />
                <h3 className="text-lg font-semibold text-gray-900">OpenAI LLM Intelligence</h3>
              </div>
              <p className="text-gray-700 text-sm leading-relaxed">
                Advanced language models provide human-level content understanding. With structured output frameworks, we get 
                validated, parseable results—not just text completions.
              </p>
            </div>

            <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
              <div className="flex items-center gap-2 mb-3">
                <Globe className="w-5 h-5 text-secondary-600" />
                <h3 className="text-lg font-semibold text-gray-900">Supabase Infrastructure</h3>
              </div>
              <p className="text-gray-700 text-sm leading-relaxed">
                PostgreSQL database with row-level security, real-time subscriptions, and built-in authentication. 
                Scales from prototype to production without infrastructure headaches.
              </p>
            </div>
          </div>

          <div className="mt-8 bg-secondary-50 border border-secondary-200 rounded-lg p-6">
            <h4 className="font-semibold text-gray-900 mb-2">Why This Stack Matters</h4>
            <p className="text-gray-700 leading-relaxed">
              A year ago, production-ready LLM APIs didn't exist. Structured outputs were experimental. The combination of 
              reliable AI services, modern web frameworks, and scalable infrastructure makes this application possible today 
              in a way it simply wasn't before. We're not just using new tools—we're solving problems that couldn't be solved.
            </p>
          </div>
        </div>
      </section>

      {/* The Future Section */}
      <section className="py-16 bg-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3 mb-8">
            <Rocket className="w-8 h-8 text-secondary-600" />
            <h2 className="text-3xl font-bold text-gray-900">What's Next</h2>
          </div>

          <div className="bg-gradient-to-br from-secondary-50 to-primary-50 rounded-xl p-8 border border-gray-200">
            <p className="text-gray-700 leading-relaxed mb-4">
              We're just scratching the surface. As LLMs improve, so does our ability to understand and analyze content. 
              Future capabilities include:
            </p>
            <ul className="space-y-2 text-gray-700">
              <li className="flex items-start gap-2">
                <span className="text-secondary-600 font-bold">•</span>
                <span>Real-time competitive content analysis and positioning recommendations</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-secondary-600 font-bold">•</span>
                <span>Automated content generation based on gaps and opportunities</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-secondary-600 font-bold">•</span>
                <span>Multi-language content analysis and translation quality scoring</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-secondary-600 font-bold">•</span>
                <span>Predictive SEO: identify ranking opportunities before your competitors</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-secondary-600 font-bold">•</span>
                <span>Brand voice training: custom AI models that understand your specific style</span>
              </li>
            </ul>
            <p className="text-gray-700 leading-relaxed mt-4">
              The convergence of web scraping, AI, and modern infrastructure isn't slowing down—it's accelerating. 
              What we're building today will seem primitive in a year. That's the point.
            </p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-gradient-to-br from-secondary-600 to-primary-600 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold mb-4">Experience What's Possible</h2>
          <p className="text-xl text-secondary-100 mb-8">
            See how AI-powered web intelligence can transform your workflow.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="/signup"
              className="px-8 py-4 bg-white text-secondary-600 rounded-lg font-semibold text-lg hover:bg-gray-100 transition-all shadow-lg"
            >
              Start Free Trial
            </a>
            <a
              href="/quick-start"
              className="px-8 py-4 bg-secondary-700 hover:bg-secondary-800 text-white rounded-lg font-semibold text-lg border-2 border-secondary-500 transition-all"
            >
              View Documentation
            </a>
          </div>
        </div>
      </section>
    </div>
  );
};

export default AboutPage;
