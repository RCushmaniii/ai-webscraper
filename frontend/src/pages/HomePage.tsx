import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const HomePage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const handleGetStarted = () => {
    if (user) {
      navigate('/crawls');
    } else {
      navigate('/login');
    }
  };

  return (
    <div className="max-w-4xl mx-auto pt-12 pb-16">
      <div className="text-center mb-16">
        <h1 className="text-5xl font-bold text-neutral-charcoal mb-6">
          Intelligent Website Analysis
        </h1>
        <p className="text-xl text-neutral-steel leading-relaxed max-w-2xl mx-auto">
          Extract clean content, analyze SEO health, and discover issues across your entire website with AI-powered crawling.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-8 mb-16">
        <div className="bg-white rounded-lg border border-primary-100 p-8 shadow-soft hover:shadow-md transition-shadow">
          <div className="flex items-center mb-4">
            <div className="bg-secondary-100 p-3 rounded-lg mr-4">
              <svg className="h-6 w-6 text-secondary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-neutral-charcoal">Simple & Fast</h2>
          </div>
          <p className="text-neutral-steel leading-relaxed">
            Enter a URL and let AI crawl your entire site automatically. Get results in minutes, not hours.
          </p>
        </div>

        <div className="bg-white rounded-lg border border-primary-100 p-8 shadow-soft hover:shadow-md transition-shadow">
          <div className="flex items-center mb-4">
            <div className="bg-secondary-100 p-3 rounded-lg mr-4">
              <svg className="h-6 w-6 text-secondary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-neutral-charcoal">Deep Insights</h2>
          </div>
          <p className="text-neutral-steel leading-relaxed">
            Extract full page content, analyze SEO metadata, detect broken links, and identify technical issues.
          </p>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-8 mb-16">
        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-secondary-500 text-white rounded-full text-2xl font-bold mb-4">1</div>
          <h3 className="text-xl font-semibold text-neutral-charcoal mb-3">Enter URL</h3>
          <p className="text-neutral-steel leading-relaxed">
            Provide any website URL to begin your analysis
          </p>
        </div>

        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-secondary-500 text-white rounded-full text-2xl font-bold mb-4">2</div>
          <h3 className="text-xl font-semibold text-neutral-charcoal mb-3">AI Crawls Site</h3>
          <p className="text-neutral-steel leading-relaxed">
            Our crawler extracts content, metadata, and identifies issues automatically
          </p>
        </div>

        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-secondary-500 text-white rounded-full text-2xl font-bold mb-4">3</div>
          <h3 className="text-xl font-semibold text-neutral-charcoal mb-3">Review & Export</h3>
          <p className="text-neutral-steel leading-relaxed">
            View detailed reports and export content for your use
          </p>
        </div>
      </div>

      <div className="text-center">
        <button
          onClick={handleGetStarted}
          className="inline-flex items-center gap-2 px-8 py-4 text-lg font-semibold text-white bg-secondary-500 hover:bg-secondary-hover rounded-lg shadow-md hover:shadow-lg transition-all"
        >
          {user ? 'Go to Crawls' : 'Get Started'}
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </button>
        {!user && (
          <p className="mt-4 text-sm text-neutral-steel">
            Already have an account?{' '}
            <Link to="/login" className="text-secondary-600 hover:text-secondary-700 font-medium">
              Sign in
            </Link>
          </p>
        )}
      </div>
    </div>
  );
};

export default HomePage;
