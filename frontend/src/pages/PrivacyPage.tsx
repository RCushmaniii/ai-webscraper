import React from 'react';

const PrivacyPage: React.FC = () => {
  return (
    <div className="container px-4 py-8 mx-auto">
      <h1 className="mb-6 text-3xl font-bold text-gray-900">Privacy Policy</h1>
      
      <div className="prose max-w-none">
        <p className="mb-4">
          Last updated: {new Date().toLocaleDateString()}
        </p>
        
        <h2 className="mt-8 mb-4 text-2xl font-semibold">1. Introduction</h2>
        <p>
          AAA WebScraper ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our web scraping and site auditing platform.
        </p>
        
        <h2 className="mt-8 mb-4 text-2xl font-semibold">2. Information We Collect</h2>
        <p>
          We collect information that you provide directly to us when you:
        </p>
        <ul className="list-disc pl-6 mb-4">
          <li>Create an account</li>
          <li>Use our services</li>
          <li>Contact our support team</li>
          <li>Respond to surveys or communications</li>
        </ul>
        
        <h2 className="mt-8 mb-4 text-2xl font-semibold">3. How We Use Your Information</h2>
        <p>
          We may use the information we collect for various purposes, including to:
        </p>
        <ul className="list-disc pl-6 mb-4">
          <li>Provide, maintain, and improve our services</li>
          <li>Process and complete transactions</li>
          <li>Send administrative information</li>
          <li>Respond to your comments, questions, and requests</li>
          <li>Protect against, identify, and prevent fraud and other illegal activity</li>
        </ul>
        
        <h2 className="mt-8 mb-4 text-2xl font-semibold">4. Data Security</h2>
        <p>
          We implement appropriate technical and organizational measures to protect the security of your personal information. However, no security system is impenetrable, and we cannot guarantee the security of our systems 100%.
        </p>
        
        <h2 className="mt-8 mb-4 text-2xl font-semibold">5. Changes to This Privacy Policy</h2>
        <p>
          We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and updating the "Last updated" date.
        </p>
        
        <h2 className="mt-8 mb-4 text-2xl font-semibold">6. Contact Us</h2>
        <p>
          If you have any questions about this Privacy Policy, please contact us at:
        </p>
        <p className="font-medium">
          privacy@aaawebscraper.com
        </p>
      </div>
    </div>
  );
};

export default PrivacyPage;
