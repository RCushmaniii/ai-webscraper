import React from 'react';
import { Cookie, Mail, Settings, Eye, Shield } from 'lucide-react';

const CookiesPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 mb-8">
          <div className="flex items-center gap-3 mb-4">
            <Cookie className="w-8 h-8 text-secondary-600" />
            <h1 className="text-4xl font-bold text-gray-900">Cookie Policy</h1>
          </div>
          <p className="text-gray-600">
            Last updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>

        {/* Content */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 space-y-8">
          {/* Introduction */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">1. What Are Cookies?</h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              Cookies are small text files that are placed on your device when you visit our website. They help us provide you with a better experience by remembering your preferences, keeping you logged in, and understanding how you use our Service.
            </p>
            <p className="text-gray-700 leading-relaxed">
              This Cookie Policy explains what cookies are, how we use them, and how you can manage your cookie preferences.
            </p>
          </section>

          {/* Types of Cookies */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">2. Types of Cookies We Use</h2>
            
            <div className="space-y-6">
              {/* Essential Cookies */}
              <div className="border-l-4 border-secondary-500 pl-4">
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="w-5 h-5 text-secondary-600" />
                  <h3 className="text-xl font-semibold text-gray-900">2.1 Essential Cookies (Required)</h3>
                </div>
                <p className="text-gray-700 mb-2">
                  These cookies are necessary for the website to function and cannot be disabled. They enable core functionality such as:
                </p>
                <ul className="list-disc pl-6 space-y-1 text-gray-700">
                  <li>Authentication and security</li>
                  <li>Session management</li>
                  <li>Load balancing</li>
                  <li>Form submission</li>
                </ul>
                <p className="text-sm text-gray-600 mt-2 italic">
                  Examples: Supabase auth tokens, session cookies
                </p>
              </div>

              {/* Functional Cookies */}
              <div className="border-l-4 border-blue-500 pl-4">
                <div className="flex items-center gap-2 mb-2">
                  <Settings className="w-5 h-5 text-blue-600" />
                  <h3 className="text-xl font-semibold text-gray-900">2.2 Functional Cookies</h3>
                </div>
                <p className="text-gray-700 mb-2">
                  These cookies enable enhanced functionality and personalization, such as:
                </p>
                <ul className="list-disc pl-6 space-y-1 text-gray-700">
                  <li>Remembering your preferences and settings</li>
                  <li>Storing your language choice</li>
                  <li>Customizing your dashboard layout</li>
                  <li>Saving your crawl configurations</li>
                </ul>
                <p className="text-sm text-gray-600 mt-2 italic">
                  You can disable these cookies, but some features may not work properly.
                </p>
              </div>

              {/* Analytics Cookies */}
              <div className="border-l-4 border-green-500 pl-4">
                <div className="flex items-center gap-2 mb-2">
                  <Eye className="w-5 h-5 text-green-600" />
                  <h3 className="text-xl font-semibold text-gray-900">2.3 Analytics Cookies</h3>
                </div>
                <p className="text-gray-700 mb-2">
                  These cookies help us understand how visitors use our website, allowing us to improve our Service:
                </p>
                <ul className="list-disc pl-6 space-y-1 text-gray-700">
                  <li>Pages visited and features used</li>
                  <li>Time spent on pages</li>
                  <li>Navigation patterns</li>
                  <li>Error tracking and performance monitoring</li>
                </ul>
                <p className="text-sm text-gray-600 mt-2 italic">
                  We use analytics to improve user experience. All data is anonymized.
                </p>
              </div>
            </div>
          </section>

          {/* Third-Party Cookies */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">3. Third-Party Cookies</h2>
            <p className="text-gray-700 mb-3">
              We use trusted third-party services that may set their own cookies:
            </p>
            <div className="space-y-4">
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <h4 className="font-semibold text-gray-900 mb-2">Supabase (Authentication & Database)</h4>
                <p className="text-gray-700 text-sm mb-2">
                  Used for secure authentication and data storage. Essential for the Service to function.
                </p>
                <a href="https://supabase.com/privacy" target="_blank" rel="noopener noreferrer" className="text-secondary-600 hover:text-secondary-700 text-sm font-medium">
                  View Supabase Privacy Policy →
                </a>
              </div>

              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <h4 className="font-semibold text-gray-900 mb-2">OpenAI (AI Analysis)</h4>
                <p className="text-gray-700 text-sm mb-2">
                  Powers our AI content analysis features. Data is processed according to OpenAI's privacy policy.
                </p>
                <a href="https://openai.com/privacy" target="_blank" rel="noopener noreferrer" className="text-secondary-600 hover:text-secondary-700 text-sm font-medium">
                  View OpenAI Privacy Policy →
                </a>
              </div>
            </div>
          </section>

          {/* Cookie Duration */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">4. How Long Do Cookies Last?</h2>
            <div className="space-y-3">
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Session Cookies</h4>
                <p className="text-gray-700">
                  Temporary cookies that are deleted when you close your browser. Used for authentication and session management.
                </p>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Persistent Cookies</h4>
                <p className="text-gray-700">
                  Remain on your device for a set period (typically 30-365 days) or until you delete them. Used for preferences and analytics.
                </p>
              </div>
            </div>
          </section>

          {/* Managing Cookies */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <Settings className="w-6 h-6 text-secondary-600" />
              <h2 className="text-2xl font-bold text-gray-900">5. How to Manage Cookies</h2>
            </div>
            
            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">5.1 Browser Settings</h3>
            <p className="text-gray-700 mb-3">
              Most web browsers allow you to control cookies through their settings. You can:
            </p>
            <ul className="list-disc pl-6 space-y-2 text-gray-700">
              <li>Block all cookies</li>
              <li>Block third-party cookies only</li>
              <li>Delete cookies when you close your browser</li>
              <li>View and delete individual cookies</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-6">5.2 Browser-Specific Instructions</h3>
            <div className="space-y-2">
              <p className="text-gray-700">
                <strong>Chrome:</strong>{' '}
                <a href="https://support.google.com/chrome/answer/95647" target="_blank" rel="noopener noreferrer" className="text-secondary-600 hover:text-secondary-700">
                  Cookie settings guide
                </a>
              </p>
              <p className="text-gray-700">
                <strong>Firefox:</strong>{' '}
                <a href="https://support.mozilla.org/en-US/kb/cookies-information-websites-store-on-your-computer" target="_blank" rel="noopener noreferrer" className="text-secondary-600 hover:text-secondary-700">
                  Cookie settings guide
                </a>
              </p>
              <p className="text-gray-700">
                <strong>Safari:</strong>{' '}
                <a href="https://support.apple.com/guide/safari/manage-cookies-sfri11471/mac" target="_blank" rel="noopener noreferrer" className="text-secondary-600 hover:text-secondary-700">
                  Cookie settings guide
                </a>
              </p>
              <p className="text-gray-700">
                <strong>Edge:</strong>{' '}
                <a href="https://support.microsoft.com/en-us/microsoft-edge/delete-cookies-in-microsoft-edge-63947406-40ac-c3b8-57b9-2a946a29ae09" target="_blank" rel="noopener noreferrer" className="text-secondary-600 hover:text-secondary-700">
                  Cookie settings guide
                </a>
              </p>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mt-4">
              <p className="text-gray-700 text-sm">
                <strong>Note:</strong> Blocking or deleting cookies may affect your ability to use certain features of our Service, including staying logged in and saving your preferences.
              </p>
            </div>
          </section>

          {/* Do Not Track */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">6. Do Not Track Signals</h2>
            <p className="text-gray-700">
              Some browsers include a "Do Not Track" (DNT) feature that signals websites you visit that you do not want to have your online activity tracked. We currently do not respond to DNT signals, but we respect your privacy choices and provide cookie management options as described above.
            </p>
          </section>

          {/* Updates to Policy */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">7. Updates to This Cookie Policy</h2>
            <p className="text-gray-700">
              We may update this Cookie Policy from time to time to reflect changes in our practices or for legal, operational, or regulatory reasons. We will notify you of any material changes by updating the "Last updated" date at the top of this policy.
            </p>
          </section>

          {/* Contact */}
          <section className="bg-gray-50 rounded-lg p-6 border border-gray-200">
            <div className="flex items-center gap-2 mb-4">
              <Mail className="w-6 h-6 text-secondary-600" />
              <h2 className="text-2xl font-bold text-gray-900">8. Contact Us</h2>
            </div>
            <p className="text-gray-700 mb-4">
              If you have questions about our use of cookies or this Cookie Policy, please contact us:
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

export default CookiesPage;
