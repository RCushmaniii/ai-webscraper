import React from 'react';

const TermsPage: React.FC = () => {
  return (
    <div className="container px-4 py-8 mx-auto">
      <h1 className="mb-6 text-3xl font-bold text-gray-900">Terms of Service</h1>
      
      <div className="prose max-w-none">
        <p className="mb-4">
          Last updated: {new Date().toLocaleDateString()}
        </p>
        
        <h2 className="mt-8 mb-4 text-2xl font-semibold">1. Acceptance of Terms</h2>
        <p>
          By accessing or using the AI WebScraper platform, you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use our services.
        </p>
        
        <h2 className="mt-8 mb-4 text-2xl font-semibold">2. Description of Service</h2>
        <p>
          AI WebScraper provides web scraping and site auditing services for authorized users. Our platform allows users to crawl websites, analyze content, and generate reports within the limits of our service parameters.
        </p>
        
        <h2 className="mt-8 mb-4 text-2xl font-semibold">3. User Responsibilities</h2>
        <p>
          As a user of our service, you agree to:
        </p>
        <ul className="list-disc pl-6 mb-4">
          <li>Provide accurate account information</li>
          <li>Maintain the security of your account credentials</li>
          <li>Use the service in compliance with all applicable laws and regulations</li>
          <li>Respect robots.txt directives and website terms of service when crawling</li>
          <li>Not use our service to scrape content you do not have permission to access</li>
          <li>Not attempt to reverse engineer or breach our platform security</li>
        </ul>
        
        <h2 className="mt-8 mb-4 text-2xl font-semibold">4. Limitation of Liability</h2>
        <p>
          AI WebScraper is provided "as is" without warranties of any kind. We are not responsible for any damages resulting from your use of our service, including but not limited to direct, indirect, incidental, punitive, and consequential damages.
        </p>
        
        <h2 className="mt-8 mb-4 text-2xl font-semibold">5. Intellectual Property</h2>
        <p>
          All content, features, and functionality of the AI WebScraper platform are owned by us and are protected by copyright, trademark, and other intellectual property laws. You may not reproduce, distribute, modify, or create derivative works of our platform without explicit permission.
        </p>
        
        <h2 className="mt-8 mb-4 text-2xl font-semibold">6. Termination</h2>
        <p>
          We reserve the right to terminate or suspend your account and access to our services at our sole discretion, without notice, for conduct that we believe violates these Terms of Service or is harmful to other users, us, or third parties, or for any other reason.
        </p>
        
        <h2 className="mt-8 mb-4 text-2xl font-semibold">7. Changes to Terms</h2>
        <p>
          We may modify these Terms of Service at any time. We will provide notice of significant changes by posting an update on our website. Your continued use of our service after such modifications constitutes your acceptance of the updated terms.
        </p>
        
        <h2 className="mt-8 mb-4 text-2xl font-semibold">8. Contact Us</h2>
        <p>
          If you have any questions about these Terms of Service, please contact us at:
        </p>
        <p className="font-medium">
          legal@aiwebscraper.com
        </p>
      </div>
    </div>
  );
};

export default TermsPage;
