import { useEffect } from 'react';

export function usePageTitle(title: string) {
  useEffect(() => {
    const base = 'AI WebScraper';
    document.title = title ? `${title} | ${base}` : base;
    return () => { document.title = base; };
  }, [title]);
}
