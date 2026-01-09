import React from 'react';
import { Link } from 'react-router-dom';
import { Github, Twitter, Linkedin, Mail, Globe } from 'lucide-react';

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gray-900 text-gray-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 mb-8">
          {/* Brand Column */}
          <div className="lg:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <Globe className="w-8 h-8 text-secondary-400" />
              <span className="text-xl font-bold text-white">AI WebScraper</span>
            </div>
            <p className="text-gray-400 mb-6 max-w-sm">
              Transform websites into actionable intelligence with AI-powered content analysis, 
              SEO recommendations, and accessibility insights.
            </p>
            <div className="flex gap-4">
              <a
                href="https://github.com/RCushmaniii/ai-webscraper"
                target="_blank"
                rel="noopener noreferrer"
                className="w-10 h-10 bg-gray-800 hover:bg-gray-700 rounded-lg flex items-center justify-center transition-colors"
                aria-label="GitHub"
              >
                <Github className="w-5 h-5" />
              </a>
              <a
                href="https://twitter.com"
                target="_blank"
                rel="noopener noreferrer"
                className="w-10 h-10 bg-gray-800 hover:bg-gray-700 rounded-lg flex items-center justify-center transition-colors"
                aria-label="Twitter"
              >
                <Twitter className="w-5 h-5" />
              </a>
              <a
                href="https://linkedin.com"
                target="_blank"
                rel="noopener noreferrer"
                className="w-10 h-10 bg-gray-800 hover:bg-gray-700 rounded-lg flex items-center justify-center transition-colors"
                aria-label="LinkedIn"
              >
                <Linkedin className="w-5 h-5" />
              </a>
              <a
                href="mailto:support@aiwebscraper.com"
                className="w-10 h-10 bg-gray-800 hover:bg-gray-700 rounded-lg flex items-center justify-center transition-colors"
                aria-label="Email"
              >
                <Mail className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Product Column */}
          <div>
            <h3 className="text-white font-semibold mb-4">Product</h3>
            <ul className="space-y-3">
              <li>
                <Link to="/quick-start" className="hover:text-white transition-colors">
                  Quick Start
                </Link>
              </li>
              <li>
                <Link to="/docs" className="hover:text-white transition-colors">
                  Documentation
                </Link>
              </li>
              <li>
                <a href="https://github.com/RCushmaniii/ai-webscraper" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">
                  API Reference
                </a>
              </li>
              <li>
                <Link to="/dashboard" className="hover:text-white transition-colors">
                  Dashboard
                </Link>
              </li>
              <li>
                <a href="#pricing" className="hover:text-white transition-colors">
                  Pricing
                </a>
              </li>
            </ul>
          </div>

          {/* Resources Column */}
          <div>
            <h3 className="text-white font-semibold mb-4">Resources</h3>
            <ul className="space-y-3">
              <li>
                <a href="https://github.com/RCushmaniii/ai-webscraper/blob/main/docs/LLM_SERVICE.md" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">
                  LLM Service Guide
                </a>
              </li>
              <li>
                <a href="https://github.com/RCushmaniii/ai-webscraper/blob/main/docs/DEPLOYMENT_PLAN.md" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">
                  Deployment Guide
                </a>
              </li>
              <li>
                <a href="https://github.com/RCushmaniii/ai-webscraper/blob/main/CHANGELOG.md" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">
                  Changelog
                </a>
              </li>
              <li>
                <a href="https://github.com/RCushmaniii/ai-webscraper/issues" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">
                  Support
                </a>
              </li>
              <li>
                <a href="#blog" className="hover:text-white transition-colors">
                  Blog
                </a>
              </li>
            </ul>
          </div>

          {/* Company Column */}
          <div>
            <h3 className="text-white font-semibold mb-4">Company</h3>
            <ul className="space-y-3">
              <li>
                <Link to="/about" className="hover:text-white transition-colors" onClick={() => window.scrollTo(0, 0)}>
                  About
                </Link>
              </li>
              <li>
                <Link to="/use-cases" className="hover:text-white transition-colors" onClick={() => window.scrollTo(0, 0)}>
                  Use Cases
                </Link>
              </li>
              <li>
                <Link to="/privacy" className="hover:text-white transition-colors" onClick={() => window.scrollTo(0, 0)}>
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link to="/terms" className="hover:text-white transition-colors" onClick={() => window.scrollTo(0, 0)}>
                  Terms of Service
                </Link>
              </li>
              <li>
                <a href="mailto:info@cushlabs.ai" className="hover:text-white transition-colors">
                  Contact
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-gray-800">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="text-sm text-gray-400">
              © {currentYear} AI WebScraper. All rights reserved. Built with ❤️ by{' '}
              <a 
                href="https://github.com/RCushmaniii" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-secondary-400 hover:text-secondary-300 transition-colors"
              >
                Robert Cushman
              </a>
            </div>
            <div className="flex gap-6 text-sm">
              <Link to="/privacy" className="hover:text-white transition-colors" onClick={() => window.scrollTo(0, 0)}>
                Privacy
              </Link>
              <Link to="/terms" className="hover:text-white transition-colors" onClick={() => window.scrollTo(0, 0)}>
                Terms
              </Link>
              <Link to="/cookies" className="hover:text-white transition-colors" onClick={() => window.scrollTo(0, 0)}>
                Cookies
              </Link>
              <a href="#sitemap" className="hover:text-white transition-colors">
                Sitemap
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
