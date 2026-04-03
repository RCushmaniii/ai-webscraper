import { useEffect } from 'react';

const BASE_TITLE = 'AI WebScraper';
const DEFAULT_DESCRIPTION = 'Crawl websites, detect SEO issues, and generate AI-powered analysis reports. Built for marketing teams and site owners who need actionable website insights.';

export function usePageTitle(title: string, description?: string) {
  useEffect(() => {
    document.title = title ? `${title} | ${BASE_TITLE}` : BASE_TITLE;

    if (description) {
      const meta = document.querySelector('meta[name="description"]');
      if (meta) {
        meta.setAttribute('content', description);
      }
      const ogDesc = document.querySelector('meta[property="og:description"]');
      if (ogDesc) {
        ogDesc.setAttribute('content', description);
      }
      const twitterDesc = document.querySelector('meta[name="twitter:description"]');
      if (twitterDesc) {
        twitterDesc.setAttribute('content', description);
      }
    }

    const ogTitle = document.querySelector('meta[property="og:title"]');
    if (ogTitle) {
      ogTitle.setAttribute('content', title ? `${title} | ${BASE_TITLE}` : `${BASE_TITLE} by CushLabs — AI-Powered Site Audits`);
    }
    const twitterTitle = document.querySelector('meta[name="twitter:title"]');
    if (twitterTitle) {
      twitterTitle.setAttribute('content', title ? `${title} | ${BASE_TITLE}` : `${BASE_TITLE} by CushLabs — AI-Powered Site Audits`);
    }

    return () => {
      document.title = BASE_TITLE;
      const meta = document.querySelector('meta[name="description"]');
      if (meta) meta.setAttribute('content', DEFAULT_DESCRIPTION);
      const ogDesc = document.querySelector('meta[property="og:description"]');
      if (ogDesc) ogDesc.setAttribute('content', DEFAULT_DESCRIPTION);
      const twitterDesc = document.querySelector('meta[name="twitter:description"]');
      if (twitterDesc) twitterDesc.setAttribute('content', DEFAULT_DESCRIPTION);
      const ogTitle = document.querySelector('meta[property="og:title"]');
      if (ogTitle) ogTitle.setAttribute('content', `${BASE_TITLE} by CushLabs — AI-Powered Site Audits`);
      const twitterTitle = document.querySelector('meta[name="twitter:title"]');
      if (twitterTitle) twitterTitle.setAttribute('content', `${BASE_TITLE} by CushLabs — AI-Powered Site Audits`);
    };
  }, [title, description]);
}
