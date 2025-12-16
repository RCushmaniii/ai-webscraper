import React from 'react';
import { Link } from 'react-router-dom';

const BatchDetailPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-4">Out of Scope (v1)</h1>
      <p className="text-gray-700 mb-6">
        Batch crawling is intentionally excluded in v1.
      </p>
      <Link to="/crawls" className="btn-primary inline-block">
        Go to Crawls
      </Link>
    </div>
  );
};

export default BatchDetailPage;
