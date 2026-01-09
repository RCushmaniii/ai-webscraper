import React from 'react';
import { FileText, Mail, AlertCircle, Scale, CreditCard, Ban } from 'lucide-react';

const TermsPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 mb-8">
          <div className="flex items-center gap-3 mb-4">
            <FileText className="w-8 h-8 text-secondary-600" />
            <h1 className="text-4xl font-bold text-gray-900">Terms of Service</h1>
          </div>
          <p className="text-gray-600">
            Last updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>

        {/* Content */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 space-y-8">
          {/* Acceptance */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">1. Acceptance of Terms</h2>
            <p className="text-gray-700 leading-relaxed">
              By accessing or using AI WebScraper (the "Service"), you agree to be bound by these Terms of Service ("Terms"). If you do not agree to these Terms, you may not access or use the Service. These Terms apply to all users, including visitors, registered users, and paying customers.
            </p>
          </section>

          {/* Service Description */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">2. Description of Service</h2>
            <p className="text-gray-700 mb-3">
              AI WebScraper is an AI-powered web intelligence platform that provides:
            </p>
            <ul className="list-disc pl-6 space-y-2 text-gray-700">
              <li>Automated website crawling and content extraction</li>
              <li>AI-powered content analysis using GPT-4</li>
              <li>SEO recommendations and optimization insights</li>
              <li>Content quality scoring and improvement suggestions</li>
              <li>Image accessibility analysis and alt text generation</li>
              <li>Semantic search and content similarity detection</li>
              <li>Executive reports and analytics dashboards</li>
            </ul>
            <p className="text-gray-700 mt-3">
              We reserve the right to modify, suspend, or discontinue any aspect of the Service at any time without prior notice.
            </p>
          </section>

          {/* User Accounts */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">3. User Accounts and Registration</h2>
            <p className="text-gray-700 mb-3">To use certain features of the Service, you must create an account. You agree to:</p>
            <ul className="list-disc pl-6 space-y-2 text-gray-700">
              <li>Provide accurate, current, and complete information during registration</li>
              <li>Maintain and promptly update your account information</li>
              <li>Maintain the security and confidentiality of your password</li>
              <li>Accept responsibility for all activities under your account</li>
              <li>Notify us immediately of any unauthorized use of your account</li>
            </ul>
            <p className="text-gray-700 mt-3">
              You may not share your account credentials or allow others to access your account. We reserve the right to suspend or terminate accounts that violate these Terms.
            </p>
          </section>

          {/* Acceptable Use */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <AlertCircle className="w-6 h-6 text-secondary-600" />
              <h2 className="text-2xl font-bold text-gray-900">4. Acceptable Use Policy</h2>
            </div>
            <p className="text-gray-700 mb-3">You agree to use the Service only for lawful purposes. You may NOT:</p>
            <ul className="list-disc pl-6 space-y-2 text-gray-700">
              <li>Crawl websites without proper authorization or in violation of robots.txt directives</li>
              <li>Access or scrape content you do not have permission to access</li>
              <li>Use the Service to collect personal information without consent</li>
              <li>Overload or interfere with the operation of websites you crawl</li>
              <li>Violate any applicable laws, regulations, or third-party rights</li>
              <li>Reverse engineer, decompile, or attempt to extract source code from our platform</li>
              <li>Use the Service to distribute malware, spam, or harmful content</li>
              <li>Resell, sublicense, or redistribute the Service without authorization</li>
              <li>Attempt to bypass rate limits, usage restrictions, or security measures</li>
              <li>Use the Service in any way that could damage our reputation or business</li>
            </ul>
            <p className="text-gray-700 mt-3">
              Violation of this Acceptable Use Policy may result in immediate termination of your account and legal action.
            </p>
          </section>

          {/* Billing and Payments */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <CreditCard className="w-6 h-6 text-secondary-600" />
              <h2 className="text-2xl font-bold text-gray-900">5. Billing and Payments</h2>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">5.1 Subscription Plans</h3>
            <p className="text-gray-700 mb-3">
              We offer various subscription plans with different features and usage limits. By subscribing, you agree to pay all applicable fees according to your selected plan.
            </p>
            
            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">5.2 Payment Terms</h3>
            <ul className="list-disc pl-6 space-y-2 text-gray-700">
              <li>Subscription fees are billed in advance on a monthly or annual basis</li>
              <li>All fees are non-refundable unless otherwise stated</li>
              <li>You authorize us to charge your payment method for all fees</li>
              <li>Prices are subject to change with 30 days notice</li>
              <li>Failed payments may result in service suspension</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">5.3 LLM Usage Costs</h3>
            <p className="text-gray-700">
              AI analysis features incur additional costs based on OpenAI API usage. You will be charged for actual usage according to our published pricing. We provide cost tracking and budget controls to help you manage expenses.
            </p>
          </section>

          {/* Intellectual Property */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <Scale className="w-6 h-6 text-secondary-600" />
              <h2 className="text-2xl font-bold text-gray-900">6. Intellectual Property Rights</h2>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">6.1 Our Rights</h3>
            <p className="text-gray-700 mb-3">
              All content, features, functionality, software, and technology of the Service are owned by CushLabs.ai and protected by copyright, trademark, patent, and other intellectual property laws. You may not:
            </p>
            <ul className="list-disc pl-6 space-y-2 text-gray-700">
              <li>Copy, modify, or create derivative works of our platform</li>
              <li>Reproduce, distribute, or publicly display our content</li>
              <li>Use our trademarks, logos, or branding without permission</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">6.2 Your Content</h3>
            <p className="text-gray-700">
              You retain ownership of any content you submit to the Service (URLs, configurations, etc.). By using the Service, you grant us a limited license to process, store, and analyze your content solely to provide the Service.
            </p>
          </section>

          {/* Disclaimers */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">7. Disclaimers and Warranties</h2>
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <p className="text-gray-700 font-medium mb-2">THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND.</p>
              <p className="text-gray-700">
                We disclaim all warranties, express or implied, including warranties of merchantability, fitness for a particular purpose, and non-infringement. We do not guarantee that the Service will be uninterrupted, secure, or error-free.
              </p>
            </div>
          </section>

          {/* Limitation of Liability */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <Ban className="w-6 h-6 text-secondary-600" />
              <h2 className="text-2xl font-bold text-gray-900">8. Limitation of Liability</h2>
            </div>
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-gray-700 mb-3">
                TO THE MAXIMUM EXTENT PERMITTED BY LAW, CUSHLABS.AI SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR ANY LOSS OF PROFITS OR REVENUES, WHETHER INCURRED DIRECTLY OR INDIRECTLY, OR ANY LOSS OF DATA, USE, GOODWILL, OR OTHER INTANGIBLE LOSSES.
              </p>
              <p className="text-gray-700">
                Our total liability shall not exceed the amount you paid us in the 12 months preceding the claim.
              </p>
            </div>
          </section>

          {/* Indemnification */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">9. Indemnification</h2>
            <p className="text-gray-700">
              You agree to indemnify, defend, and hold harmless CushLabs.ai, its affiliates, and their respective officers, directors, employees, and agents from any claims, liabilities, damages, losses, and expenses arising from your use of the Service, violation of these Terms, or infringement of any third-party rights.
            </p>
          </section>

          {/* Termination */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">10. Termination</h2>
            <p className="text-gray-700 mb-3">
              Either party may terminate your account at any time:
            </p>
            <ul className="list-disc pl-6 space-y-2 text-gray-700">
              <li><strong>You may cancel</strong> your subscription at any time through your account settings</li>
              <li><strong>We may suspend or terminate</strong> your account for violation of these Terms, non-payment, or any other reason at our sole discretion</li>
              <li><strong>Upon termination,</strong> your right to use the Service immediately ceases, and we may delete your data after 30 days</li>
            </ul>
          </section>

          {/* Governing Law */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">11. Governing Law and Disputes</h2>
            <p className="text-gray-700 mb-3">
              These Terms shall be governed by and construed in accordance with the laws of the United States, without regard to conflict of law principles. Any disputes arising from these Terms or the Service shall be resolved through binding arbitration, except where prohibited by law.
            </p>
          </section>

          {/* Changes to Terms */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">12. Changes to These Terms</h2>
            <p className="text-gray-700">
              We may modify these Terms at any time. We will provide notice of material changes by email or through the Service. Your continued use of the Service after changes become effective constitutes acceptance of the modified Terms. If you do not agree to the changes, you must stop using the Service.
            </p>
          </section>

          {/* Miscellaneous */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">13. Miscellaneous</h2>
            <ul className="list-disc pl-6 space-y-2 text-gray-700">
              <li><strong>Entire Agreement:</strong> These Terms constitute the entire agreement between you and CushLabs.ai</li>
              <li><strong>Severability:</strong> If any provision is found unenforceable, the remaining provisions remain in effect</li>
              <li><strong>No Waiver:</strong> Our failure to enforce any right or provision does not constitute a waiver</li>
              <li><strong>Assignment:</strong> You may not assign these Terms; we may assign them without restriction</li>
            </ul>
          </section>

          {/* Contact */}
          <section className="bg-gray-50 rounded-lg p-6 border border-gray-200">
            <div className="flex items-center gap-2 mb-4">
              <Mail className="w-6 h-6 text-secondary-600" />
              <h2 className="text-2xl font-bold text-gray-900">14. Contact Us</h2>
            </div>
            <p className="text-gray-700 mb-4">
              If you have any questions about these Terms of Service, please contact us:
            </p>
            <div className="space-y-2">
              <p className="text-gray-700">
                <strong>Email:</strong>{' '}
                <a href="mailto:info@cushlabs.ai" className="text-secondary-600 hover:text-secondary-700 font-medium">
                  info@cushlabs.ai
                </a>
              </p>
              <p className="text-gray-700">
                <strong>Company:</strong> CushLabs.ai
              </p>
              <p className="text-gray-700">
                <strong>Product:</strong> AI WebScraper
              </p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default TermsPage;
