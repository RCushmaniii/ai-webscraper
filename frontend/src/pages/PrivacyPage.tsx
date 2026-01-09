import React from 'react';
import { Mail, Shield, Lock, Eye, Database, UserCheck } from 'lucide-react';

const PrivacyPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 mb-8">
          <div className="flex items-center gap-3 mb-4">
            <Shield className="w-8 h-8 text-secondary-600" />
            <h1 className="text-4xl font-bold text-gray-900">Privacy Policy</h1>
          </div>
          <p className="text-gray-600">
            Last updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>

        {/* Content */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 space-y-8">
          {/* Introduction */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">1. Introduction</h2>
            <p className="text-gray-700 leading-relaxed">
              AI WebScraper ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our AI-powered web intelligence platform. By using our services, you agree to the collection and use of information in accordance with this policy.
            </p>
          </section>

          {/* Information We Collect */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <Database className="w-6 h-6 text-secondary-600" />
              <h2 className="text-2xl font-bold text-gray-900">2. Information We Collect</h2>
            </div>
            
            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">2.1 Information You Provide</h3>
            <p className="text-gray-700 mb-3">We collect information that you provide directly to us, including:</p>
            <ul className="list-disc pl-6 space-y-2 text-gray-700">
              <li><strong>Account Information:</strong> Email address, password, and profile details</li>
              <li><strong>Crawl Data:</strong> URLs you submit for analysis, crawl configurations, and preferences</li>
              <li><strong>Payment Information:</strong> Billing details and transaction history (processed securely through third-party payment processors)</li>
              <li><strong>Communications:</strong> Messages, feedback, and support requests you send to us</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">2.2 Automatically Collected Information</h3>
            <p className="text-gray-700 mb-3">When you use our services, we automatically collect:</p>
            <ul className="list-disc pl-6 space-y-2 text-gray-700">
              <li><strong>Usage Data:</strong> Pages visited, features used, time spent, and interaction patterns</li>
              <li><strong>Device Information:</strong> Browser type, operating system, IP address, and device identifiers</li>
              <li><strong>Cookies:</strong> Session data, preferences, and analytics information (see our Cookie Policy)</li>
              <li><strong>API Usage:</strong> LLM analysis requests, cost tracking, and service performance metrics</li>
            </ul>
          </section>

          {/* How We Use Your Information */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <Eye className="w-6 h-6 text-secondary-600" />
              <h2 className="text-2xl font-bold text-gray-900">3. How We Use Your Information</h2>
            </div>
            <p className="text-gray-700 mb-3">We use the collected information for the following purposes:</p>
            <ul className="list-disc pl-6 space-y-2 text-gray-700">
              <li><strong>Service Delivery:</strong> Provide, maintain, and improve our AI-powered web analysis platform</li>
              <li><strong>AI Processing:</strong> Analyze websites using GPT-4 and generate content insights, SEO recommendations, and accessibility reports</li>
              <li><strong>Account Management:</strong> Create and manage your account, process payments, and provide customer support</li>
              <li><strong>Communication:</strong> Send service updates, security alerts, and respond to your inquiries</li>
              <li><strong>Analytics:</strong> Understand usage patterns, improve features, and optimize performance</li>
              <li><strong>Security:</strong> Detect and prevent fraud, abuse, and unauthorized access</li>
              <li><strong>Legal Compliance:</strong> Comply with applicable laws, regulations, and legal processes</li>
            </ul>
          </section>

          {/* Data Sharing */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">4. How We Share Your Information</h2>
            <p className="text-gray-700 mb-3">We do not sell your personal information. We may share your information with:</p>
            <ul className="list-disc pl-6 space-y-2 text-gray-700">
              <li><strong>Service Providers:</strong> Third-party vendors who help us operate our platform (e.g., Supabase for database, OpenAI for AI analysis)</li>
              <li><strong>Payment Processors:</strong> Secure payment gateways to process transactions</li>
              <li><strong>Legal Requirements:</strong> When required by law, court order, or government request</li>
              <li><strong>Business Transfers:</strong> In connection with a merger, acquisition, or sale of assets</li>
              <li><strong>With Your Consent:</strong> When you explicitly authorize us to share your information</li>
            </ul>
          </section>

          {/* Data Security */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <Lock className="w-6 h-6 text-secondary-600" />
              <h2 className="text-2xl font-bold text-gray-900">5. Data Security</h2>
            </div>
            <p className="text-gray-700 mb-3">
              We implement industry-standard security measures to protect your information:
            </p>
            <ul className="list-disc pl-6 space-y-2 text-gray-700">
              <li>Encryption of data in transit (TLS/SSL) and at rest</li>
              <li>Secure authentication with Supabase Auth</li>
              <li>Row-level security (RLS) policies in our database</li>
              <li>Regular security audits and vulnerability assessments</li>
              <li>Access controls and monitoring systems</li>
            </ul>
            <p className="text-gray-700 mt-3">
              However, no method of transmission over the Internet or electronic storage is 100% secure. While we strive to protect your information, we cannot guarantee absolute security.
            </p>
          </section>

          {/* Your Rights */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <UserCheck className="w-6 h-6 text-secondary-600" />
              <h2 className="text-2xl font-bold text-gray-900">6. Your Rights and Choices</h2>
            </div>
            <p className="text-gray-700 mb-3">You have the following rights regarding your personal information:</p>
            <ul className="list-disc pl-6 space-y-2 text-gray-700">
              <li><strong>Access:</strong> Request a copy of the personal information we hold about you</li>
              <li><strong>Correction:</strong> Update or correct inaccurate information</li>
              <li><strong>Deletion:</strong> Request deletion of your account and associated data</li>
              <li><strong>Portability:</strong> Export your data in a machine-readable format</li>
              <li><strong>Opt-Out:</strong> Unsubscribe from marketing communications</li>
              <li><strong>Cookies:</strong> Manage cookie preferences through your browser settings</li>
            </ul>
            <p className="text-gray-700 mt-3">
              To exercise these rights, please contact us at <a href="mailto:info@cushlabs.ai" className="text-secondary-600 hover:text-secondary-700 font-medium">info@cushlabs.ai</a>
            </p>
          </section>

          {/* Data Retention */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">7. Data Retention</h2>
            <p className="text-gray-700">
              We retain your personal information for as long as necessary to provide our services and comply with legal obligations. When you delete your account, we will delete or anonymize your personal information within 30 days, except where we are required to retain it for legal or regulatory purposes.
            </p>
          </section>

          {/* International Transfers */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">8. International Data Transfers</h2>
            <p className="text-gray-700">
              Your information may be transferred to and processed in countries other than your country of residence. We ensure appropriate safeguards are in place to protect your information in accordance with this Privacy Policy and applicable data protection laws.
            </p>
          </section>

          {/* Children's Privacy */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">9. Children's Privacy</h2>
            <p className="text-gray-700">
              Our services are not intended for individuals under the age of 18. We do not knowingly collect personal information from children. If you believe we have collected information from a child, please contact us immediately.
            </p>
          </section>

          {/* Changes to Policy */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">10. Changes to This Privacy Policy</h2>
            <p className="text-gray-700">
              We may update this Privacy Policy from time to time to reflect changes in our practices or legal requirements. We will notify you of material changes by posting the updated policy on this page and updating the "Last updated" date. Your continued use of our services after changes constitutes acceptance of the updated policy.
            </p>
          </section>

          {/* Contact */}
          <section className="bg-gray-50 rounded-lg p-6 border border-gray-200">
            <div className="flex items-center gap-2 mb-4">
              <Mail className="w-6 h-6 text-secondary-600" />
              <h2 className="text-2xl font-bold text-gray-900">11. Contact Us</h2>
            </div>
            <p className="text-gray-700 mb-4">
              If you have any questions, concerns, or requests regarding this Privacy Policy or our data practices, please contact us:
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

export default PrivacyPage;
