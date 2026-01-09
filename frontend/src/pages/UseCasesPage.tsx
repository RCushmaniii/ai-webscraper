import React from 'react';
import { CheckCircle, ArrowRight, TrendingUp, Clock, DollarSign, Users, Zap } from 'lucide-react';

const UseCasesPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-secondary-50 via-white to-primary-50 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
              Real-World Use Cases
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
              See how professionals across industries use AI WebScraper to save time, reduce costs, 
              and deliver better results for their clients and teams.
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
                From 3-Week Audits to Same-Day Delivery
              </h2>
              <p className="text-lg text-gray-700 mb-6 leading-relaxed">
                A mid-sized SEO agency was spending 20+ hours per client audit, manually reviewing pages, 
                checking meta tags, and writing recommendations. They could only handle 4 clients per month.
              </p>

              <div className="space-y-4 mb-8">
                <div className="flex items-start gap-3">
                  <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0 mt-1" />
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">The Challenge</h3>
                    <p className="text-gray-600">
                      Client sites averaged 200-500 pages. Manual review meant clicking through every page, 
                      taking notes, and compiling reports in spreadsheets.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0 mt-1" />
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">The Solution</h3>
                    <p className="text-gray-600">
                      AI WebScraper crawls 500 pages in 30 minutes, analyzes content quality, generates SEO 
                      recommendations, and identifies issues automatically.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0 mt-1" />
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">The Results</h3>
                    <p className="text-gray-600">
                      Audits now take 2 hours instead of 20. The agency handles 12 clients per month, 
                      tripling revenue without hiring more staff.
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 p-6 bg-gray-50 rounded-lg border border-gray-200">
                <div>
                  <div className="flex items-center gap-2 text-green-600 font-bold text-2xl mb-1">
                    <TrendingUp className="w-5 h-5" />
                    3x
                  </div>
                  <div className="text-sm text-gray-600">More Clients</div>
                </div>
                <div>
                  <div className="flex items-center gap-2 text-green-600 font-bold text-2xl mb-1">
                    <Clock className="w-5 h-5" />
                    90%
                  </div>
                  <div className="text-sm text-gray-600">Time Saved</div>
                </div>
                <div>
                  <div className="flex items-center gap-2 text-green-600 font-bold text-2xl mb-1">
                    <DollarSign className="w-5 h-5" />
                    $45k
                  </div>
                  <div className="text-sm text-gray-600">Added Revenue/mo</div>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-8 border border-blue-200">
              <h3 className="text-xl font-semibold text-gray-900 mb-6">Before vs After</h3>
              
              <div className="space-y-6">
                <div>
                  <div className="text-sm font-medium text-gray-500 mb-2">BEFORE</div>
                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <ul className="space-y-2 text-sm text-gray-700">
                      <li>• 20 hours per audit</li>
                      <li>• 4 clients per month</li>
                      <li>• $8,000/month revenue</li>
                      <li>• Manual spreadsheet reports</li>
                      <li>• Limited scalability</li>
                    </ul>
                  </div>
                </div>

                <div className="flex justify-center">
                  <ArrowRight className="w-6 h-6 text-blue-600" />
                </div>

                <div>
                  <div className="text-sm font-medium text-gray-500 mb-2">AFTER</div>
                  <div className="bg-white rounded-lg p-4 border border-green-200">
                    <ul className="space-y-2 text-sm text-gray-700">
                      <li className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        2 hours per audit
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        12 clients per month
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        $24,000/month revenue
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        AI-powered reports
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        Unlimited scalability
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Use Case 2: Enterprise Content Team */}
      <section className="py-20 bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="order-2 lg:order-1">
              <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-8 border border-purple-200">
                <h3 className="text-xl font-semibold text-gray-900 mb-6">Real Example</h3>
                
                <div className="bg-white rounded-lg p-6 border border-gray-200 mb-6">
                  <div className="text-sm font-medium text-purple-600 mb-2">SCENARIO</div>
                  <p className="text-gray-700 mb-4">
                    E-commerce company with 2,000 product pages needed to ensure consistent brand voice 
                    and identify low-quality content before a major marketing campaign.
                  </p>
                  
                  <div className="text-sm font-medium text-purple-600 mb-2">MANUAL APPROACH</div>
                  <p className="text-gray-700 mb-4">
                    Would require 3 content editors × 40 hours each = 120 hours of work. 
                    Cost: $6,000 in labor.
                  </p>
                  
                  <div className="text-sm font-medium text-green-600 mb-2">AI WEBSCRAPER APPROACH</div>
                  <p className="text-gray-700">
                    Crawl and analyze all 2,000 pages in 3 hours. Get quality scores, brand voice consistency 
                    ratings, and specific improvement recommendations. Cost: $14 in LLM usage.
                  </p>
                </div>

                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="font-semibold text-gray-900 mb-2">ROI Calculation</div>
                  <div className="space-y-1 text-sm text-gray-700">
                    <div className="flex justify-between">
                      <span>Time saved:</span>
                      <span className="font-medium">117 hours</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Cost saved:</span>
                      <span className="font-medium">$5,986</span>
                    </div>
                    <div className="flex justify-between border-t border-green-300 pt-2 mt-2">
                      <span className="font-bold">ROI:</span>
                      <span className="font-bold text-green-600">42,757%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="order-1 lg:order-2">
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-100 text-purple-700 rounded-full text-sm font-medium mb-4">
                Enterprise Content Team
              </div>
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
                Maintaining Quality Across 2,000 Pages
              </h2>
              <p className="text-lg text-gray-700 mb-6 leading-relaxed">
                Large organizations struggle to maintain consistent content quality across thousands of pages. 
                Manual review is impossible at scale.
              </p>

              <div className="space-y-4 mb-8">
                <div className="flex items-start gap-3">
                  <Zap className="w-6 h-6 text-purple-600 flex-shrink-0 mt-1" />
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">Automated Quality Scoring</h3>
                    <p className="text-gray-600">
                      Every page gets a 0-100 quality score based on clarity, relevance, engagement, and structure. 
                      Instantly identify which pages need attention.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Zap className="w-6 h-6 text-purple-600 flex-shrink-0 mt-1" />
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">Brand Voice Consistency</h3>
                    <p className="text-gray-600">
                      AI analyzes tone, style, and messaging across all pages. Flag inconsistencies and 
                      ensure your brand voice is uniform.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Zap className="w-6 h-6 text-purple-600 flex-shrink-0 mt-1" />
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">Content Gap Analysis</h3>
                    <p className="text-gray-600">
                      Identify missing topics, duplicate content, and opportunities for new pages based on 
                      semantic analysis of your entire site.
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
                <div className="font-semibold text-gray-900 mb-3">Key Metrics</div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-2xl font-bold text-purple-600">2,000</div>
                    <div className="text-sm text-gray-600">Pages Analyzed</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-purple-600">3 hrs</div>
                    <div className="text-sm text-gray-600">Total Time</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-purple-600">$14</div>
                    <div className="text-sm text-gray-600">LLM Cost</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-purple-600">97%</div>
                    <div className="text-sm text-gray-600">Time Saved</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Use Case 3: Accessibility Consultant */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-100 text-green-700 rounded-full text-sm font-medium mb-4">
                Accessibility Consultant
              </div>
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
                WCAG Compliance in Hours, Not Months
              </h2>
              <p className="text-lg text-gray-700 mb-6 leading-relaxed">
                A university website with 800 pages and 3,500 images needed WCAG 2.1 AA compliance. 
                Writing alt text manually would take months.
              </p>

              <div className="space-y-6">
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="font-semibold text-gray-900 mb-2">The Problem</div>
                  <ul className="space-y-2 text-sm text-gray-700">
                    <li>• 3,500 images missing alt text</li>
                    <li>• Manual writing: 30 seconds per image</li>
                    <li>• Total time: 29 hours of tedious work</li>
                    <li>• Risk of legal action for non-compliance</li>
                  </ul>
                </div>

                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="font-semibold text-gray-900 mb-2">The AI Solution</div>
                  <ul className="space-y-2 text-sm text-gray-700">
                    <li className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                      AI generates contextual alt text for all 3,500 images
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                      Identifies decorative vs. content images
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                      Provides confidence scores for review
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                      Completed in 2 hours instead of 29
                    </li>
                  </ul>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="font-semibold text-gray-900 mb-2">Quality Results</div>
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-600">High Confidence (90%+)</span>
                        <span className="font-medium">2,800 images</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-green-600 h-2 rounded-full" style={{width: '80%'}}></div>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-600">Medium Confidence (70-89%)</span>
                        <span className="font-medium">600 images</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-yellow-600 h-2 rounded-full" style={{width: '17%'}}></div>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-600">Needs Review (&lt;70%)</span>
                        <span className="font-medium">100 images</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-red-600 h-2 rounded-full" style={{width: '3%'}}></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-green-50 to-teal-50 rounded-2xl p-8 border border-green-200">
              <h3 className="text-xl font-semibold text-gray-900 mb-6">Workflow Comparison</h3>
              
              <div className="space-y-6">
                <div>
                  <div className="text-sm font-medium text-gray-500 mb-3">TRADITIONAL APPROACH</div>
                  <div className="space-y-3">
                    <div className="bg-white rounded-lg p-3 border border-gray-200">
                      <div className="flex items-center gap-2 mb-1">
                        <Clock className="w-4 h-4 text-gray-400" />
                        <span className="text-sm font-medium text-gray-900">Week 1-2</span>
                      </div>
                      <p className="text-sm text-gray-600">Manually review each image, understand context</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-gray-200">
                      <div className="flex items-center gap-2 mb-1">
                        <Clock className="w-4 h-4 text-gray-400" />
                        <span className="text-sm font-medium text-gray-900">Week 3-4</span>
                      </div>
                      <p className="text-sm text-gray-600">Write alt text for 3,500 images</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-gray-200">
                      <div className="flex items-center gap-2 mb-1">
                        <Clock className="w-4 h-4 text-gray-400" />
                        <span className="text-sm font-medium text-gray-900">Week 5</span>
                      </div>
                      <p className="text-sm text-gray-600">Quality review and corrections</p>
                    </div>
                  </div>
                  <div className="mt-3 text-sm text-gray-600 font-medium">
                    Total: 5 weeks, $4,500 in labor
                  </div>
                </div>

                <div className="flex justify-center">
                  <div className="w-full border-t-2 border-dashed border-gray-300"></div>
                </div>

                <div>
                  <div className="text-sm font-medium text-gray-500 mb-3">AI WEBSCRAPER APPROACH</div>
                  <div className="space-y-3">
                    <div className="bg-white rounded-lg p-3 border border-green-200">
                      <div className="flex items-center gap-2 mb-1">
                        <Zap className="w-4 h-4 text-green-600" />
                        <span className="text-sm font-medium text-gray-900">Hour 1</span>
                      </div>
                      <p className="text-sm text-gray-600">Crawl site and extract all images with context</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-green-200">
                      <div className="flex items-center gap-2 mb-1">
                        <Zap className="w-4 h-4 text-green-600" />
                        <span className="text-sm font-medium text-gray-900">Hour 2</span>
                      </div>
                      <p className="text-sm text-gray-600">AI generates alt text for all 3,500 images</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-green-200">
                      <div className="flex items-center gap-2 mb-1">
                        <Zap className="w-4 h-4 text-green-600" />
                        <span className="text-sm font-medium text-gray-900">Day 2-3</span>
                      </div>
                      <p className="text-sm text-gray-600">Review 100 low-confidence suggestions</p>
                    </div>
                  </div>
                  <div className="mt-3 text-sm text-green-600 font-medium">
                    Total: 3 days, $35 in costs (AI + review)
                  </div>
                </div>
              </div>

              <div className="mt-6 bg-white rounded-lg p-4 border border-green-300">
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600 mb-1">93%</div>
                  <div className="text-sm text-gray-600">Faster Compliance</div>
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
              Turning One-Time Projects Into Recurring Revenue
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              A web dev agency built sites but had no recurring revenue. Now they offer monthly content audits 
              as a premium service, generating $15k/month in additional revenue.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mb-4">
                <Users className="w-6 h-6 text-orange-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">The Opportunity</h3>
              <p className="text-gray-600 mb-4">
                After launching a client's site, offer ongoing content monitoring as a premium service. 
                Most clients say yes to $500-1,000/month for peace of mind.
              </p>
              <div className="text-sm text-orange-600 font-medium">
                10 clients × $750/mo = $7,500 MRR
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mb-4">
                <TrendingUp className="w-6 h-6 text-orange-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">What They Deliver</h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                  Monthly content quality reports
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                  SEO health monitoring
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                  Accessibility compliance checks
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                  Broken link detection
                </li>
              </ul>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mb-4">
                <DollarSign className="w-6 h-6 text-orange-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">The Economics</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Client pays:</span>
                  <span className="font-medium text-gray-900">$750/month</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">AI WebScraper cost:</span>
                  <span className="font-medium text-gray-900">$15/month</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Time spent:</span>
                  <span className="font-medium text-gray-900">30 minutes</span>
                </div>
                <div className="flex justify-between border-t border-gray-200 pt-3 mt-3">
                  <span className="text-gray-900 font-semibold">Profit margin:</span>
                  <span className="font-bold text-green-600">98%</span>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-12 bg-gradient-to-br from-orange-50 to-yellow-50 rounded-2xl p-8 border border-orange-200">
            <div className="text-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Real Numbers from a Real Agency</h3>
              <p className="text-gray-600">After 6 months of offering content monitoring services</p>
            </div>
            <div className="grid md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="text-4xl font-bold text-orange-600 mb-2">20</div>
                <div className="text-sm text-gray-600">Clients Enrolled</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-orange-600 mb-2">$15k</div>
                <div className="text-sm text-gray-600">Monthly Recurring Revenue</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-orange-600 mb-2">10hrs</div>
                <div className="text-sm text-gray-600">Total Time Per Month</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-orange-600 mb-2">95%</div>
                <div className="text-sm text-gray-600">Client Retention Rate</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-br from-secondary-600 to-primary-600 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Ready to Write Your Own Success Story?
          </h2>
          <p className="text-xl text-secondary-100 mb-8">
            Join professionals who've transformed their workflow with AI-powered web intelligence.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="/signup"
              className="px-8 py-4 bg-white text-secondary-600 rounded-lg font-semibold text-lg hover:bg-gray-100 transition-all shadow-lg"
            >
              Start Free Trial
            </a>
            <a
              href="/about"
              className="px-8 py-4 bg-secondary-700 hover:bg-secondary-800 text-white rounded-lg font-semibold text-lg border-2 border-secondary-500 transition-all"
            >
              Learn More
            </a>
          </div>
          <p className="mt-6 text-sm text-secondary-100">
            14-day free trial • No credit card required • See results in minutes
          </p>
        </div>
      </section>
    </div>
  );
};

export default UseCasesPage;
