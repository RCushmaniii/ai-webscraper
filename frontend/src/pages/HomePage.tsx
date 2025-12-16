import React from 'react';
import { Link } from 'react-router-dom';

const HomePage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-primary-800 mb-4">
          Site Analysis (Internal Tool)
        </h1>
        <p className="text-xl text-gray-600">
          Crawl a site, store clean page content with metadata, and surface high-signal issues and priorities.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-8 mb-12">
        <div className="card">
          <div className="flex items-center mb-4">
            <div className="bg-primary-100 p-3 rounded-full mr-4">
              <svg className="h-6 w-6 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-gray-800">Easy to Use</h2>
          </div>
          <p className="text-gray-600">
            Start a crawl from a single URL and inspect the resulting page inventory.
          </p>
        </div>

        <div className="card">
          <div className="flex items-center mb-4">
            <div className="bg-primary-100 p-3 rounded-full mr-4">
              <svg className="h-6 w-6 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-gray-800">Powerful Features</h2>
          </div>
          <p className="text-gray-600">
            Content-first extraction, lightweight importance signals, and obvious issue detection.
          </p>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-6 mb-12">
        <div className="card text-center">
          <div className="text-4xl font-bold text-primary-600 mb-2">1</div>
          <h3 className="text-xl font-semibold mb-2">Enter URL</h3>
          <p className="text-gray-600">
            Provide the start URL you want to analyze
          </p>
        </div>

        <div className="card text-center">
          <div className="text-4xl font-bold text-primary-600 mb-2">2</div>
          <h3 className="text-xl font-semibold mb-2">Run Crawl</h3>
          <p className="text-gray-600">
            Crawl the site and extract clean page text with basic metadata
          </p>
        </div>

        <div className="card text-center">
          <div className="text-4xl font-bold text-primary-600 mb-2">3</div>
          <h3 className="text-xl font-semibold mb-2">Review Findings</h3>
          <p className="text-gray-600">
            Sort by importance and review high-signal issues
          </p>
        </div>
      </div>

      <div className="text-center">
        <Link to="/login" className="btn-primary inline-block px-8 py-3 text-lg">
          Sign In
        </Link>
      </div>
    </div>
  );
};

export default HomePage;
