import React, { useState, useEffect, useMemo } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { RefreshCw, ChevronUp, ChevronDown, Download, ExternalLink, FileText, AlertTriangle, AlertCircle, Info, CheckCircle } from 'lucide-react';
import { apiService, Crawl, Page, Link as CrawlLink, Issue, Image } from '../services/api';
import ConfirmationModal from '../components/ConfirmationModal';
import SearchBar from '../components/SearchBar';

// Issue type descriptions - educational "why" content
const ISSUE_DESCRIPTIONS: Record<string, { description: string; impact: 'seo' | 'ux' | 'compliance' | 'performance' }> = {
  'SEO': {
    description: 'SEO issues affect how search engines understand and rank your pages.',
    impact: 'seo'
  },
  'Accessibility': {
    description: 'Accessibility issues make your site difficult or impossible to use for people with disabilities.',
    impact: 'compliance'
  },
  'Performance': {
    description: 'Performance issues slow down your site, hurting user experience and SEO rankings.',
    impact: 'performance'
  },
  'Content Quality': {
    description: 'Content quality issues indicate pages that may not provide enough value to visitors.',
    impact: 'seo'
  },
  'Technical': {
    description: 'Technical issues can prevent search engines from properly crawling and indexing your site.',
    impact: 'seo'
  },
  'Crawl Error': {
    description: 'Pages that failed to load during crawling - may indicate server issues or broken pages.',
    impact: 'ux'
  }
};

// Specific issue message descriptions
const ISSUE_MESSAGE_DESCRIPTIONS: Record<string, string> = {
  'Missing title tag': 'Title tags are the #1 on-page SEO factor. Without them, search engines cannot properly index your pages.',
  'Title too short': 'Short titles miss opportunities to include keywords and may not be descriptive enough for search results.',
  'Title too long': 'Titles over 60 characters get truncated in search results, potentially hiding important information.',
  'Missing meta description': 'Meta descriptions appear in search results. Missing ones mean Google will auto-generate text, often poorly.',
  'Meta description too short': 'Short descriptions may not entice users to click through from search results.',
  'Meta description too long': 'Descriptions over 160 characters get truncated in search results.',
  'Missing H1 heading': 'H1 tags help search engines understand the main topic of your page. Every page should have exactly one.',
  'Multiple H1 headings': 'Multiple H1s confuse search engines about your page\'s primary topic. Use only one H1 per page.',
  'missing alt text': 'Images without alt text are invisible to screen readers and search engines miss context about your visuals.',
  'Missing viewport meta tag': 'Without viewport meta, your site won\'t display properly on mobile devices.',
  'Missing lang attribute': 'The lang attribute helps screen readers pronounce content correctly and aids SEO for international sites.',
  'Thin content': 'Pages with very little content may be seen as low-quality by search engines.',
  'Large page size': 'Large pages take longer to load, hurting both user experience and search rankings.'
};

const CrawlDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [crawl, setCrawl] = useState<Crawl | null>(null);
  const [pages, setPages] = useState<Page[]>([]);
  const [links, setLinks] = useState<CrawlLink[]>([]);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [images, setImages] = useState<Image[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('pages');
  const [pageLoading, setPageLoading] = useState(false);
  const [linkFilter, setLinkFilter] = useState<'all' | 'internal' | 'external'>('all');
  const [linkStatusFilter, setLinkStatusFilter] = useState<'all' | 'working' | 'broken'>('all');
  const [imageAltFilter, setImageAltFilter] = useState<'all' | 'with_alt' | 'missing_alt'>('all');
  const [imageBrokenFilter, setImageBrokenFilter] = useState<'all' | 'working' | 'broken'>('all');
  const [pageStatusFilter, setPageStatusFilter] = useState<'all' | 'main' | '2xx' | '3xx' | '4xx' | '5xx'>('all');
  const [deleting, setDeleting] = useState(false);
  const [rerunning, setRerunning] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showRerunConfirm, setShowRerunConfirm] = useState(false);
  const [showStopConfirm, setShowStopConfirm] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [pageSort, setPageSort] = useState<string>('status_code');
  const [pageSortDir, setPageSortDir] = useState<'asc' | 'desc'>('asc');
  const [linkSort, setLinkSort] = useState<string>('anchor_text');
  const [linkSortDir, setLinkSortDir] = useState<'asc' | 'desc'>('asc');
  const [imageSort, setImageSort] = useState<string>('has_alt');
  const [imageSortDir, setImageSortDir] = useState<'asc' | 'desc'>('asc');
  const [issueSort, setIssueSort] = useState<string>('severity');
  const [issueSortDir, setIssueSortDir] = useState<'asc' | 'desc'>('desc');
  const [issueSeverityFilter, setIssueSeverityFilter] = useState<'all' | 'critical' | 'high' | 'medium' | 'low'>('all');
  const [issueTypeFilter, setIssueTypeFilter] = useState<string>('all');
  const [issueImpactFilter, setIssueImpactFilter] = useState<'all' | 'seo' | 'ux' | 'compliance' | 'performance'>('all');
  const [expandedIssueCards, setExpandedIssueCards] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!id) return;
    
    const fetchCrawlData = async () => {
      try {
        setLoading(true);
        
        // Fetch crawl details
        const crawlData = await apiService.getCrawl(id);
        setCrawl(crawlData);
 
        // Always fetch page inventory (v1 core dataset)
        try {
          const pagesData = await apiService.getCrawlPages(id);
          setPages(pagesData);
        } catch (err) {
          console.error('Error fetching pages:', err);
        }
        
      } catch (err) {
        console.error('Error fetching crawl:', err);
        setError('Failed to load crawl data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchCrawlData();
  }, [id]);

  const fetchTabData = async (tab: string) => {
    if (!id) return;
    
    setPageLoading(true);
    
    try {
      switch (tab) {
        case 'pages':
          if (pages.length === 0) {
            const pagesData = await apiService.getCrawlPages(id);
            setPages(pagesData);
          }
          break;
        case 'links':
          if (links.length === 0) {
            const linksData = await apiService.getCrawlLinks(id);
            setLinks(linksData);
          }
          break;
        case 'issues':
          if (issues.length === 0) {
            const issuesData = await apiService.getCrawlIssues(id);
            setIssues(issuesData);
          }
          break;
        case 'images':
          if (images.length === 0) {
            const imagesData = await apiService.getCrawlImages(id);
            setImages(imagesData);
          }
          break;
        default:
          break;
      }
    } catch (err) {
      console.error(`Error fetching ${tab}:`, err);
      setError(`Failed to load ${tab} data. Please try again later.`);
    } finally {
      setPageLoading(false);
    }
  };

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    fetchTabData(tab);
  };

  const handleDelete = async () => {
    if (!id) return;

    setDeleting(true);
    try {
      await apiService.deleteCrawl(id);
      navigate('/crawls');
    } catch (err) {
      console.error('Error deleting crawl:', err);
      setError('Failed to delete crawl. Please try again.');
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  const handleStopCrawl = async () => {
    if (!crawl || !id) return;
    setShowStopConfirm(false);
    setStopping(true);

    try {
      await apiService.stopCrawl(id);
      toast.success('Crawl stopped successfully');
      // Refresh crawl data to show updated status
      const crawlData = await apiService.getCrawl(id);
      setCrawl(crawlData);
    } catch (err) {
      console.error('Error stopping crawl:', err);
      toast.error('Failed to stop crawl');
    } finally {
      setStopping(false);
    }
  };

  const handleRerun = async () => {
    if (!crawl) return;
    setShowRerunConfirm(false);
    setRerunning(true);

    try {
      // Remove existing suffixes (counter, timestamp, or "(Re-run)")
      let baseName = crawl.name
        .replace(/\s*\(Re-run\)\s*/g, '')  // Remove "(Re-run)"
        .replace(/\s*#\d+\s*-\s*.+$/, '')   // Remove "#2 - Jan 15, 2:30 PM"
        .replace(/\s*#\d+$/, '')            // Remove trailing "#2"
        .trim();

      // Fetch all crawls to determine next counter
      const allCrawls = await apiService.getCrawls();

      // Find all crawls with this base name
      const pattern = new RegExp(`^${baseName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(\\s*#(\\d+))?`, 'i');
      const matchingCrawls = allCrawls.filter(c => pattern.test(c.name));

      // Determine next counter number
      const existingNumbers = matchingCrawls
        .map(c => {
          const match = c.name.match(/#(\d+)/);
          return match ? parseInt(match[1], 10) : 1;
        });

      const nextNumber = existingNumbers.length > 0 ? Math.max(...existingNumbers) + 1 : 2;

      // Create timestamp
      const timestamp = new Date().toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });

      // Create new name: "My Crawl #2 - Jan 15, 02:30 PM"
      const newName = `${baseName} #${nextNumber} - ${timestamp}`;

      await apiService.createCrawl({
        url: crawl.url,
        name: newName,
        max_depth: crawl.max_depth,
        max_pages: crawl.max_pages,
        respect_robots_txt: crawl.respect_robots_txt,
        follow_external_links: crawl.follow_external_links,
        js_rendering: crawl.js_rendering,
        rate_limit: crawl.rate_limit,
        user_agent: crawl.user_agent
      });
      toast.success('Crawl re-run initiated successfully');
      navigate('/crawls');
    } catch (err) {
      console.error('Error re-running crawl:', err);
      toast.error('Failed to re-run crawl');
    } finally {
      setRerunning(false);
    }
  };

  const handlePageSort = (column: string) => {
    if (pageSort === column) {
      // Cycle through: asc -> desc -> neutral
      if (pageSortDir === 'asc') {
        setPageSortDir('desc');
      } else {
        // Reset to neutral (no sorting)
        setPageSort('');
        setPageSortDir('asc');
      }
    } else {
      setPageSort(column);
      setPageSortDir('asc');
    }
  };

  const handleLinkSort = (column: string) => {
    if (linkSort === column) {
      // Cycle through: asc -> desc -> neutral
      if (linkSortDir === 'asc') {
        setLinkSortDir('desc');
      } else {
        // Reset to neutral (no sorting)
        setLinkSort('');
        setLinkSortDir('asc');
      }
    } else {
      setLinkSort(column);
      setLinkSortDir('asc');
    }
  };

  const handleImageSort = (column: string) => {
    if (imageSort === column) {
      // Cycle through: asc -> desc -> neutral
      if (imageSortDir === 'asc') {
        setImageSortDir('desc');
      } else {
        // Reset to neutral (no sorting)
        setImageSort('');
        setImageSortDir('asc');
      }
    } else {
      setImageSort(column);
      setImageSortDir('asc');
    }
  };

  const handleIssueSort = (column: string) => {
    if (issueSort === column) {
      // Cycle through: asc -> desc -> neutral
      if (issueSortDir === 'asc') {
        setIssueSortDir('desc');
      } else {
        // Reset to neutral (no sorting)
        setIssueSort('');
        setIssueSortDir('asc');
      }
    } else {
      setIssueSort(column);
      setIssueSortDir('asc');
    }
  };

  const getSortedPages = () => {
    let filtered = [...pages];

    // Apply status filter
    if (pageStatusFilter !== 'all') {
      filtered = filtered.filter(page => {
        const status = page.status_code;
        switch (pageStatusFilter) {
          case 'main': return page.is_primary === true;
          case '2xx': return status >= 200 && status < 300;
          case '3xx': return status >= 300 && status < 400;
          case '4xx': return status >= 400 && status < 500;
          case '5xx': return status >= 500;
          default: return true;
        }
      });
    }

    // If no sort column selected, return filtered without sorting
    if (!pageSort) {
      return filtered;
    }

    const multiplier = pageSortDir === 'asc' ? 1 : -1;

    switch (pageSort) {
      case 'title':
        return filtered.sort((a, b) => multiplier * (a.title || '').localeCompare(b.title || ''));
      case 'url':
        return filtered.sort((a, b) => multiplier * a.url.localeCompare(b.url));
      case 'status_code':
        return filtered.sort((a, b) => multiplier * (a.status_code - b.status_code));
      case 'load_time':
        return filtered.sort((a, b) => multiplier * ((a.load_time_ms || 0) - (b.load_time_ms || 0)));
      default:
        return filtered;
    }
  };

  const getSortedLinks = () => {
    let filtered = linkFilter === 'all'
      ? links
      : linkFilter === 'internal'
        ? links.filter(l => l.is_internal)
        : links.filter(l => !l.is_internal);

    // Apply status filter
    if (linkStatusFilter !== 'all') {
      filtered = filtered.filter(link => {
        if (linkStatusFilter === 'broken') {
          return link.is_broken || (link.status_code && (link.status_code >= 400));
        } else { // working
          return !link.is_broken && (!link.status_code || (link.status_code >= 200 && link.status_code < 400));
        }
      });
    }

    // If no sort column selected, return filtered without sorting
    if (!linkSort) {
      return filtered;
    }

    const sorted = [...filtered];
    const multiplier = linkSortDir === 'asc' ? 1 : -1;

    switch (linkSort) {
      case 'source_url':
        return sorted.sort((a, b) => multiplier * (a.source_url || '').localeCompare(b.source_url || ''));
      case 'anchor_text':
        return sorted.sort((a, b) => multiplier * (a.anchor_text || '').localeCompare(b.anchor_text || ''));
      case 'target_url':
        return sorted.sort((a, b) => multiplier * (a.target_url || a.url || '').localeCompare(b.target_url || b.url || ''));
      case 'type':
        return sorted.sort((a, b) => multiplier * (a.is_internal === b.is_internal ? 0 : a.is_internal ? -1 : 1));
      case 'status_code':
        return sorted.sort((a, b) => multiplier * ((a.status_code || 0) - (b.status_code || 0)));
      default:
        return sorted;
    }
  };

  const getSortedImages = () => {
    let filtered = [...images];

    // Apply alt text filter
    if (imageAltFilter !== 'all') {
      filtered = filtered.filter(image => {
        if (imageAltFilter === 'with_alt') return image.has_alt;
        if (imageAltFilter === 'missing_alt') return !image.has_alt;
        return true;
      });
    }

    // Apply broken filter
    if (imageBrokenFilter !== 'all') {
      filtered = filtered.filter(image => {
        if (imageBrokenFilter === 'broken') return image.is_broken;
        if (imageBrokenFilter === 'working') return !image.is_broken;
        return true;
      });
    }

    // If no sort column selected, return filtered without sorting
    if (!imageSort) {
      return filtered;
    }

    const sorted = [...filtered];
    const multiplier = imageSortDir === 'asc' ? 1 : -1;

    switch (imageSort) {
      case 'src':
        return sorted.sort((a, b) => multiplier * a.src.localeCompare(b.src));
      case 'alt':
        return sorted.sort((a, b) => multiplier * (a.alt || '').localeCompare(b.alt || ''));
      case 'status':
        return sorted.sort((a, b) => multiplier * (a.is_broken === b.is_broken ? 0 : a.is_broken ? 1 : -1));
      default:
        return sorted;
    }
  };

  const getSortedIssues = () => {
    let filtered = [...issues];

    // Apply severity filter
    if (issueSeverityFilter !== 'all') {
      filtered = filtered.filter(issue => issue.severity === issueSeverityFilter);
    }

    // Apply type filter
    if (issueTypeFilter !== 'all') {
      filtered = filtered.filter(issue => issue.type === issueTypeFilter);
    }

    // If no sort column selected, return filtered without sorting
    if (!issueSort) {
      return filtered;
    }

    const sorted = [...filtered];
    const multiplier = issueSortDir === 'asc' ? 1 : -1;

    // Severity order for sorting
    const severityOrder: { [key: string]: number } = {
      'critical': 4,
      'high': 3,
      'medium': 2,
      'low': 1
    };

    switch (issueSort) {
      case 'severity':
        return sorted.sort((a, b) => multiplier * ((severityOrder[a.severity] || 0) - (severityOrder[b.severity] || 0)));
      case 'type':
        return sorted.sort((a, b) => multiplier * a.type.localeCompare(b.type));
      case 'message':
        return sorted.sort((a, b) => multiplier * a.message.localeCompare(b.message));
      case 'context':
        return sorted.sort((a, b) => multiplier * (a.context || '').localeCompare(b.context || ''));
      default:
        return sorted;
    }
  };

  const SortIcon = ({ column, currentSort, currentDir }: { column: string; currentSort: string; currentDir: 'asc' | 'desc' }) => {
    if (column !== currentSort) return null;
    return currentDir === 'asc' ? <ChevronUp className="w-4 h-4 inline ml-1" /> : <ChevronDown className="w-4 h-4 inline ml-1" />;
  };

  // Aggregate issues by message pattern (e.g., "Missing title tag" appears on X pages)
  const aggregatedIssues = useMemo(() => {
    // Group issues by their message (normalized)
    const grouped = new Map<string, {
      key: string;
      type: string;
      severity: 'critical' | 'high' | 'medium' | 'low';
      message: string;
      count: number;
      pageCount: number;
      pages: Set<string>;
      issues: Issue[];
      impact: 'seo' | 'ux' | 'compliance' | 'performance';
    }>();

    issues.forEach(issue => {
      // Normalize the message to group similar issues
      const normalizedMessage = issue.message
        .replace(/\d+/g, 'X')  // Replace numbers with X
        .replace(/: .+$/, '')   // Remove specific details after colon
        .trim();

      const key = `${issue.type}-${normalizedMessage}`;

      if (!grouped.has(key)) {
        // Find the impact category
        const typeInfo = ISSUE_DESCRIPTIONS[issue.type];
        const impact = typeInfo?.impact || 'seo';

        grouped.set(key, {
          key,
          type: issue.type,
          severity: issue.severity,
          message: issue.message.replace(/: .+$/, '').trim(), // Clean message
          count: 0,
          pageCount: 0,
          pages: new Set(),
          issues: [],
          impact
        });
      }

      const group = grouped.get(key)!;
      group.count++;
      group.issues.push(issue);
      if (issue.context) {
        group.pages.add(issue.context);
      }
      group.pageCount = group.pages.size;

      // Keep the highest severity in the group
      const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
      if (severityOrder[issue.severity] > severityOrder[group.severity]) {
        group.severity = issue.severity;
      }
    });

    // Convert to array and sort by severity then count
    return Array.from(grouped.values()).sort((a, b) => {
      const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
      const severityDiff = severityOrder[b.severity] - severityOrder[a.severity];
      if (severityDiff !== 0) return severityDiff;
      return b.count - a.count;
    });
  }, [issues]);

  // Filter aggregated issues
  const filteredAggregatedIssues = useMemo(() => {
    return aggregatedIssues.filter(group => {
      if (issueSeverityFilter !== 'all' && group.severity !== issueSeverityFilter) return false;
      if (issueTypeFilter !== 'all' && group.type !== issueTypeFilter) return false;
      if (issueImpactFilter !== 'all' && group.impact !== issueImpactFilter) return false;
      return true;
    });
  }, [aggregatedIssues, issueSeverityFilter, issueTypeFilter, issueImpactFilter]);

  // Calculate site health score (0-100)
  const siteHealthScore = useMemo(() => {
    if (pages.length === 0) return 100;

    let score = 100;
    const criticalCount = issues.filter(i => i.severity === 'critical').length;
    const highCount = issues.filter(i => i.severity === 'high').length;
    const mediumCount = issues.filter(i => i.severity === 'medium').length;
    const lowCount = issues.filter(i => i.severity === 'low').length;

    // Deduct points based on severity and count
    score -= Math.min(40, criticalCount * 10);  // Up to -40 for critical
    score -= Math.min(30, highCount * 5);        // Up to -30 for high
    score -= Math.min(20, mediumCount * 2);      // Up to -20 for medium
    score -= Math.min(10, lowCount * 1);         // Up to -10 for low

    return Math.max(0, score);
  }, [issues, pages.length]);

  // Toggle expanded state for issue cards
  const toggleIssueCard = (key: string) => {
    setExpandedIssueCards(prev => {
      const newSet = new Set(prev);
      if (newSet.has(key)) {
        newSet.delete(key);
      } else {
        newSet.add(key);
      }
      return newSet;
    });
  };

  // Get description for an issue message
  const getIssueDescription = (message: string): string => {
    // Check for partial matches in the message
    for (const [key, description] of Object.entries(ISSUE_MESSAGE_DESCRIPTIONS)) {
      if (message.toLowerCase().includes(key.toLowerCase())) {
        return description;
      }
    }
    return '';
  };

  // Get specific instances for an issue type (actual images, links, pages - not summaries)
  const getIssueInstances = (issueGroup: typeof aggregatedIssues[0]): {
    type: 'images' | 'links' | 'pages' | 'generic';
    items: any[];
    columns: { key: string; label: string; render?: (item: any) => React.ReactNode }[];
  } => {
    const message = issueGroup.message.toLowerCase();

    // Missing alt text → Show actual images without alt
    if (message.includes('alt text') || message.includes('missing alt')) {
      const imagesWithoutAlt = images.filter(img => !img.has_alt);
      return {
        type: 'images',
        items: imagesWithoutAlt,
        columns: [
          {
            key: 'src',
            label: 'Image',
            render: (img) => (
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gray-100 rounded overflow-hidden flex-shrink-0">
                  <img
                    src={img.src}
                    alt=""
                    className="w-full h-full object-cover"
                    onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                  />
                </div>
                <span className="text-sm text-gray-700 truncate max-w-[200px]" title={img.src}>
                  {img.src.split('/').pop() || img.src}
                </span>
              </div>
            )
          },
          {
            key: 'page_url',
            label: 'Found On',
            render: (img) => {
              const page = pages.find(p => p.id === img.page_id);
              const pageUrl = page?.url || 'Unknown page';
              return pageUrl.startsWith('http') ? (
                <a
                  href={pageUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-secondary-600 hover:underline flex items-center gap-1"
                >
                  <span className="truncate max-w-[200px]">{pageUrl.replace(/^https?:\/\/[^/]+/, '') || '/'}</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              ) : (
                <span className="text-sm text-gray-500">{pageUrl}</span>
              );
            }
          }
        ]
      };
    }

    // Broken links → Show actual broken links
    if (message.includes('broken') && issueGroup.type !== 'Crawl Error') {
      const brokenLinks = links.filter(link => link.is_broken);
      return {
        type: 'links',
        items: brokenLinks,
        columns: [
          {
            key: 'target_url',
            label: 'Broken URL',
            render: (link) => (
              <div className="text-sm">
                <span className="text-red-600 truncate block max-w-[250px]" title={link.target_url || link.url}>
                  {(link.target_url || link.url || 'Unknown URL').substring(0, 50)}
                </span>
                {link.status_code && (
                  <span className="text-xs text-gray-400">Status: {link.status_code}</span>
                )}
              </div>
            )
          },
          {
            key: 'source',
            label: 'Found On',
            render: (link) => {
              const sourceUrl = link.source_url || 'Unknown page';
              return sourceUrl.startsWith('http') ? (
                <a
                  href={sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-secondary-600 hover:underline flex items-center gap-1"
                >
                  <span className="truncate max-w-[200px]">{sourceUrl.replace(/^https?:\/\/[^/]+/, '') || '/'}</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              ) : (
                <span className="text-sm text-gray-500">{sourceUrl}</span>
              );
            }
          },
          {
            key: 'anchor_text',
            label: 'Link Text',
            render: (link) => (
              <span className="text-sm text-gray-600 truncate block max-w-[150px]">
                {link.anchor_text || 'No text'}
              </span>
            )
          }
        ]
      };
    }

    // SEO issues (title, meta, h1) → Show pages with those issues
    if (message.includes('title') || message.includes('meta description') || message.includes('h1')) {
      // Get unique page URLs from the issues in this group
      const affectedPageUrls = new Set(issueGroup.issues.map(i => i.context).filter(Boolean));
      const affectedPages = pages.filter(p => affectedPageUrls.has(p.url));

      return {
        type: 'pages',
        items: affectedPages.length > 0 ? affectedPages : issueGroup.issues,
        columns: [
          {
            key: 'page',
            label: 'Affected Page',
            render: (item) => {
              const url = item.url || item.context || 'Unknown';
              const title = item.title || 'Untitled';
              return (
                <div>
                  <div className="text-sm font-medium text-gray-900 truncate max-w-[250px]">{title}</div>
                  {url.startsWith('http') ? (
                    <a
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-secondary-600 hover:underline flex items-center gap-1"
                    >
                      <span className="truncate max-w-[200px]">{url.replace(/^https?:\/\/[^/]+/, '') || '/'}</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  ) : (
                    <span className="text-xs text-gray-500">{url}</span>
                  )}
                </div>
              );
            }
          },
          {
            key: 'issue',
            label: 'Issue',
            render: (item) => {
              // Find the specific issue for this page
              const pageIssue = issueGroup.issues.find(i => i.context === (item.url || item.context));
              return (
                <span className="text-sm text-gray-600">
                  {pageIssue?.message || issueGroup.message}
                </span>
              );
            }
          }
        ]
      };
    }

    // Generic fallback - show pages from issue context
    const affectedPageUrls = new Set(issueGroup.issues.map(i => i.context).filter(Boolean));
    const affectedPages = pages.filter(p => affectedPageUrls.has(p.url));

    return {
      type: 'generic',
      items: affectedPages.length > 0 ? affectedPages : issueGroup.issues,
      columns: [
        {
          key: 'page',
          label: 'Affected Page',
          render: (item) => {
            const url = item.url || item.context || 'Unknown';
            return url.startsWith('http') ? (
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-secondary-600 hover:underline flex items-center gap-1"
              >
                <span className="truncate max-w-[300px]">{url.replace(/^https?:\/\/[^/]+/, '') || '/'}</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            ) : (
              <span className="text-sm text-gray-500">{url}</span>
            );
          }
        },
        {
          key: 'details',
          label: 'Details',
          render: (item) => {
            const issue = issueGroup.issues.find(i => i.context === (item.url || item.context));
            return (
              <span className="text-sm text-gray-600">
                {issue?.message || item.message || issueGroup.message}
              </span>
            );
          }
        }
      ]
    };
  };

  const exportToCSV = (data: any[], filename: string, columns: { key: string; label: string }[]) => {
    // Create CSV header
    const header = columns.map(col => col.label).join(',');

    // Create CSV rows
    const rows = data.map(item =>
      columns.map(col => {
        const value = item[col.key];
        // Escape quotes and wrap in quotes if contains comma
        const stringValue = String(value ?? '');
        if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
          return `"${stringValue.replace(/"/g, '""')}"`;
        }
        return stringValue;
      }).join(',')
    );

    // Combine header and rows
    const csv = [header, ...rows].join('\n');

    // Create blob and download
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    toast.success(`Exported ${data.length} rows to ${filename}`);
  };

  const handleExportPages = () => {
    const sortedPages = getSortedPages();
    exportToCSV(
      sortedPages,
      `pages_${crawl?.name || 'export'}_${new Date().toISOString().split('T')[0]}.csv`,
      [
        { key: 'title', label: 'Title' },
        { key: 'url', label: 'URL' },
        { key: 'status_code', label: 'Status Code' },
        { key: 'load_time_ms', label: 'Load Time (ms)' },
        { key: 'content_type', label: 'Content Type' },
        { key: 'crawl_depth', label: 'Depth' }
      ]
    );
  };

  const handleExportLinks = () => {
    const sortedLinks = getSortedLinks();
    exportToCSV(
      sortedLinks,
      `links_${crawl?.name || 'export'}_${new Date().toISOString().split('T')[0]}.csv`,
      [
        { key: 'source_url', label: 'Source URL' },
        { key: 'target_url', label: 'Target URL' },
        { key: 'anchor_text', label: 'Anchor Text' },
        { key: 'is_internal', label: 'Is Internal' },
        { key: 'status_code', label: 'Status Code' }
      ]
    );
  };

  const handleExportImages = () => {
    const sortedImages = getSortedImages();
    exportToCSV(
      sortedImages,
      `images_${crawl?.name || 'export'}_${new Date().toISOString().split('T')[0]}.csv`,
      [
        { key: 'src', label: 'Source URL' },
        { key: 'alt', label: 'Alt Text' },
        { key: 'has_alt', label: 'Has Alt' },
        { key: 'width', label: 'Width' },
        { key: 'height', label: 'Height' },
        { key: 'is_broken', label: 'Is Broken' },
        { key: 'status_code', label: 'Status Code' }
      ]
    );
  };

  const handleExportIssues = () => {
    const sortedIssues = getSortedIssues();
    exportToCSV(
      sortedIssues,
      `issues_${crawl?.name || 'export'}_${new Date().toISOString().split('T')[0]}.csv`,
      [
        { key: 'type', label: 'Type' },
        { key: 'severity', label: 'Severity' },
        { key: 'message', label: 'Message' },
        { key: 'context', label: 'Context/Page' },
        { key: 'created_at', label: 'Detected At' }
      ]
    );
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'queued':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const calculateDuration = (startDate: string, endDate?: string) => {
    if (!endDate) return 'In progress...';

    const start = new Date(startDate);
    const end = new Date(endDate);
    const durationMs = end.getTime() - start.getTime();

    const hours = Math.floor(durationMs / (1000 * 60 * 60));
    const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((durationMs % (1000 * 60)) / 1000);

    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    } else {
      return `${seconds}s`;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg font-medium text-gray-500">Loading crawl data...</div>
      </div>
    );
  }

  if (error || !crawl) {
    return (
      <div className="container px-4 py-8 mx-auto">
        <div className="p-4 mb-6 text-sm text-red-700 bg-red-100 rounded-md" role="alert">
          {error || 'Crawl not found'}
        </div>
        <Link to="/crawls" className="text-secondary-500 hover:text-secondary-600">
          &larr; Back to Crawls
        </Link>
      </div>
    );
  }

  return (
    <div className="container px-4 py-8 mx-auto">
      <div className="mb-6">
        <Link to="/crawls" className="text-secondary-500 hover:text-secondary-600">
          &larr; Back to Crawls
        </Link>
      </div>

      <div className="mb-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">{crawl.name}</h1>
          <div className="flex items-center gap-3">
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusBadgeClass(crawl.status)}`}>
              {crawl.status}
            </span>
            <button
              onClick={() => setShowRerunConfirm(true)}
              disabled={rerunning}
              className="px-4 py-2 text-sm font-medium text-white bg-secondary-600 rounded-md hover:bg-secondary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-secondary-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              {rerunning ? 'Re-running...' : 'Re-run'}
            </button>
            {(crawl.status === 'running' || crawl.status === 'queued') && (
              <button
                onClick={() => setShowStopConfirm(true)}
                disabled={stopping}
                className="px-4 py-2 text-sm font-medium text-white bg-yellow-600 rounded-md hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {stopping ? 'Stopping...' : 'Stop Crawl'}
              </button>
            )}
            <button
              onClick={() => setShowDeleteConfirm(true)}
              disabled={deleting}
              className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {deleting ? 'Deleting...' : 'Delete Crawl'}
            </button>
          </div>
        </div>
        <p className="mt-2 text-gray-600">
          <span className="font-medium">URL:</span> {crawl.url}
        </p>
        <div className="grid grid-cols-1 gap-4 mt-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6">
          <div className="p-3 bg-gray-50 rounded-md">
            <span className="text-sm text-gray-500">Created</span>
            <p className="text-gray-800 text-sm">{formatDate(crawl.created_at)}</p>
          </div>
          {crawl.status === 'completed' || crawl.status === 'failed' ? (
            <>
              <div className="p-3 bg-gray-50 rounded-md">
                <span className="text-sm text-gray-500">Finished</span>
                <p className="text-gray-800 text-sm">
                  {(crawl as any).completed_at ? formatDate((crawl as any).completed_at) : 'N/A'}
                </p>
              </div>
              <div className="p-3 bg-gray-50 rounded-md">
                <span className="text-sm text-gray-500">Duration</span>
                <p className="text-gray-800 font-medium">
                  {calculateDuration(crawl.created_at, (crawl as any).completed_at)}
                </p>
              </div>
            </>
          ) : null}
          <div className="p-3 bg-gray-50 rounded-md">
            <span className="text-sm text-gray-500">Max Depth</span>
            <p className="text-gray-800">{crawl.max_depth}</p>
          </div>
          <div className="p-3 bg-gray-50 rounded-md">
            <span className="text-sm text-gray-500">Max Pages</span>
            <p className="text-gray-800">{crawl.max_pages}</p>
          </div>
          <div className="p-3 bg-gray-50 rounded-md">
            <span className="text-sm text-gray-500">JS Rendering</span>
            <p className="text-gray-800">{crawl.js_rendering ? 'Enabled' : 'Disabled'}</p>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="mb-6 flex justify-center">
        <SearchBar crawlId={id!} />
      </div>

      {/* Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="flex -mb-px space-x-8">
          <button
            onClick={() => handleTabChange('pages')}
            className={`py-4 text-sm font-medium border-b-2 ${
              activeTab === 'pages'
                ? 'border-secondary-500 text-secondary-500'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Pages
          </button>
          <button
            onClick={() => handleTabChange('links')}
            className={`py-4 text-sm font-medium border-b-2 ${
              activeTab === 'links'
                ? 'border-secondary-500 text-secondary-500'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Links
          </button>
          <button
            onClick={() => handleTabChange('issues')}
            className={`py-4 text-sm font-medium border-b-2 ${
              activeTab === 'issues'
                ? 'border-secondary-500 text-secondary-500'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Issues
          </button>
          <button
            onClick={() => handleTabChange('images')}
            className={`py-4 text-sm font-medium border-b-2 ${
              activeTab === 'images'
                ? 'border-secondary-500 text-secondary-500'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Images
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-lg shadow">
        {pageLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-lg font-medium text-gray-500">Loading data...</div>
          </div>
        ) : (
          <>
            {/* Pages Tab */}
            {activeTab === 'pages' && (
              <div className="p-6">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-xl font-semibold text-gray-800">Crawled Pages</h2>
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <label className="text-sm text-gray-600">Filter:</label>
                      <select
                        value={pageStatusFilter}
                        onChange={(e) => setPageStatusFilter(e.target.value as any)}
                        className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="all">All Status ({pages.length})</option>
                        <option value="main">Main Pages ({pages.filter(p => p.is_primary).length})</option>
                        <option value="2xx">2xx Success ({pages.filter(p => p.status_code >= 200 && p.status_code < 300).length})</option>
                        <option value="3xx">3xx Redirect ({pages.filter(p => p.status_code >= 300 && p.status_code < 400).length})</option>
                        <option value="4xx">4xx Client Error ({pages.filter(p => p.status_code >= 400 && p.status_code < 500).length})</option>
                        <option value="5xx">5xx Server Error ({pages.filter(p => p.status_code >= 500).length})</option>
                      </select>
                    </div>
                    <button
                      onClick={handleExportPages}
                      className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                    >
                      <Download className="w-4 h-4" />
                      Export CSV
                    </button>
                  </div>
                </div>

                {pages.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th
                            onClick={() => handlePageSort('title')}
                            className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase cursor-pointer hover:bg-gray-100 select-none"
                          >
                            Title <SortIcon column="title" currentSort={pageSort} currentDir={pageSortDir} />
                          </th>
                          <th
                            onClick={() => handlePageSort('url')}
                            className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase cursor-pointer hover:bg-gray-100 select-none"
                          >
                            URL <SortIcon column="url" currentSort={pageSort} currentDir={pageSortDir} />
                          </th>
                          <th
                            onClick={() => handlePageSort('status_code')}
                            className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase cursor-pointer hover:bg-gray-100 select-none"
                          >
                            Status <SortIcon column="status_code" currentSort={pageSort} currentDir={pageSortDir} />
                          </th>
                          <th
                            onClick={() => handlePageSort('load_time')}
                            className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase cursor-pointer hover:bg-gray-100 select-none"
                          >
                            Load Time (ms) <SortIcon column="load_time" currentSort={pageSort} currentDir={pageSortDir} />
                          </th>
                          <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {getSortedPages().map((page) => (
                          <tr key={page.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4">
                              <div className="text-sm font-medium text-gray-900">{page.title || 'No title'}</div>
                            </td>
                            <td className="px-6 py-4">
                              <a 
                                href={page.url} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-sm text-secondary-600 hover:text-secondary-700 underline truncate max-w-xs block" 
                                title={page.url}
                              >
                                {page.url}
                              </a>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                page.status_code >= 200 && page.status_code < 300
                                  ? 'bg-green-100 text-green-800'
                                  : page.status_code >= 300 && page.status_code < 400
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : 'bg-red-100 text-red-800'
                              }`}>
                                {page.status_code}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-gray-500">{page.load_time_ms || 'N/A'}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <Link
                                to={`/crawls/${id}/pages/${page.id}`}
                                className="text-sm font-medium text-secondary-600 hover:text-secondary-700"
                              >
                                View Content
                              </Link>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="p-4 text-sm text-gray-700 bg-gray-100 rounded-md">
                    <p>No pages found for this crawl.</p>
                  </div>
                )}
              </div>
            )}

            {/* Links Tab */}
            {activeTab === 'links' && (
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-gray-800">Links</h2>
                  <div className="flex gap-4">
                    <div className="flex gap-2">
                      <button
                        onClick={() => setLinkFilter('all')}
                        className={`px-4 py-2 text-sm font-medium rounded-md ${
                          linkFilter === 'all'
                            ? 'bg-secondary-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        All Links ({links.length})
                      </button>
                      <button
                        onClick={() => setLinkFilter('internal')}
                        className={`px-4 py-2 text-sm font-medium rounded-md ${
                          linkFilter === 'internal'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        Internal ({links.filter(l => l.is_internal).length})
                      </button>
                      <button
                        onClick={() => setLinkFilter('external')}
                        className={`px-4 py-2 text-sm font-medium rounded-md ${
                          linkFilter === 'external'
                            ? 'bg-purple-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        External ({links.filter(l => !l.is_internal).length})
                      </button>
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="text-sm text-gray-600">Status:</label>
                      <select
                        value={linkStatusFilter}
                        onChange={(e) => setLinkStatusFilter(e.target.value as any)}
                        className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="all">All</option>
                        <option value="working">Working</option>
                        <option value="broken">Broken</option>
                      </select>
                    </div>
                    <button
                      onClick={handleExportLinks}
                      className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                    >
                      <Download className="w-4 h-4" />
                      Export CSV
                    </button>
                  </div>
                </div>

                {links.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th
                            onClick={() => handleLinkSort('source_url')}
                            className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase cursor-pointer hover:bg-gray-100 select-none"
                          >
                            Source <SortIcon column="source_url" currentSort={linkSort} currentDir={linkSortDir} />
                          </th>
                          <th
                            onClick={() => handleLinkSort('target_url')}
                            className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase cursor-pointer hover:bg-gray-100 select-none"
                          >
                            Target <SortIcon column="target_url" currentSort={linkSort} currentDir={linkSortDir} />
                          </th>
                          <th
                            onClick={() => handleLinkSort('anchor_text')}
                            className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase cursor-pointer hover:bg-gray-100 select-none"
                          >
                            Anchor Text <SortIcon column="anchor_text" currentSort={linkSort} currentDir={linkSortDir} />
                          </th>
                          <th
                            onClick={() => handleLinkSort('type')}
                            className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase cursor-pointer hover:bg-gray-100 select-none"
                          >
                            Type <SortIcon column="type" currentSort={linkSort} currentDir={linkSortDir} />
                          </th>
                          <th
                            onClick={() => handleLinkSort('status_code')}
                            className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase cursor-pointer hover:bg-gray-100 select-none"
                          >
                            Status <SortIcon column="status_code" currentSort={linkSort} currentDir={linkSortDir} />
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {getSortedLinks().map((link) => {
                          // Find the page by source_page_id (UUID reference)
                          const sourcePage = pages.find(p => p.id === link.source_page_id);
                          // Get the display URL - either from source_url field or from the matched page
                          const sourceUrl = link.source_url || sourcePage?.url;

                          return (
                            <tr key={link.id} className="hover:bg-gray-50">
                              <td className="px-6 py-4">
                                <div className="flex items-center gap-2">
                                  {sourcePage ? (
                                    <Link
                                      to={`/crawls/${id}/pages/${sourcePage.id}`}
                                      className="p-1.5 text-secondary-600 hover:text-secondary-700 hover:bg-secondary-50 rounded transition-colors"
                                      title={`View source page: ${sourcePage.url}`}
                                    >
                                      <FileText className="w-4 h-4" />
                                    </Link>
                                  ) : (
                                    <span className="p-1.5 text-gray-300" title="Source page not found in crawl data">
                                      <FileText className="w-4 h-4" />
                                    </span>
                                  )}
                                  <span className="text-sm text-gray-500 truncate max-w-[200px]" title={sourceUrl || 'Unknown'}>
                                    {sourceUrl ? (() => {
                                      try {
                                        return new URL(sourceUrl).pathname || '/';
                                      } catch {
                                        return sourceUrl;
                                      }
                                    })() : (sourcePage ? sourcePage.title || 'Untitled' : 'Unknown')}
                                  </span>
                                </div>
                              </td>
                              <td className="px-6 py-4">
                                {(() => {
                                  const targetUrl = link.target_url || link.url || '';
                                  return targetUrl ? (
                                    <a
                                      href={targetUrl}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="flex items-center gap-1.5 text-sm text-secondary-600 hover:text-secondary-700 group"
                                      title={targetUrl}
                                    >
                                      <span className="truncate max-w-[250px]">{targetUrl}</span>
                                      <ExternalLink className="w-3.5 h-3.5 flex-shrink-0 opacity-50 group-hover:opacity-100" />
                                    </a>
                                  ) : (
                                    <span className="text-sm text-gray-400">No URL</span>
                                  );
                                })()}
                              </td>
                              <td className="px-6 py-4">
                                <div className="text-sm text-gray-900 truncate max-w-xs" title={link.anchor_text}>
                                  {link.anchor_text || 'No text'}
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                  link.is_internal
                                    ? 'bg-blue-100 text-blue-800'
                                    : 'bg-purple-100 text-purple-800'
                                }`}>
                                  {link.is_internal ? 'Internal' : 'External'}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                {link.is_broken ? (
                                  <span className="inline-flex px-2 py-1 text-xs font-semibold text-red-800 bg-red-100 rounded-full">
                                    Broken {link.status_code ? `(${link.status_code})` : ''}
                                  </span>
                                ) : (
                                  <span className="inline-flex px-2 py-1 text-xs font-semibold text-green-800 bg-green-100 rounded-full">
                                    OK {link.status_code ? `(${link.status_code})` : ''}
                                  </span>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="p-4 text-sm text-gray-700 bg-gray-100 rounded-md">
                    <p>No links found for this crawl.</p>
                  </div>
                )}
              </div>
            )}

            {/* Issues Tab - Command Center */}
            {activeTab === 'issues' && (
              <div className="p-6">
                {/* Site Health Score Widget */}
                <div className="mb-6 p-6 bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl border border-gray-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-6">
                      {/* Health Score Gauge */}
                      <div className="relative w-24 h-24">
                        <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 36 36">
                          <path
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke="#e5e7eb"
                            strokeWidth="3"
                          />
                          <path
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke={siteHealthScore >= 80 ? '#22c55e' : siteHealthScore >= 60 ? '#eab308' : siteHealthScore >= 40 ? '#f97316' : '#ef4444'}
                            strokeWidth="3"
                            strokeDasharray={`${siteHealthScore}, 100`}
                          />
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className={`text-2xl font-bold ${siteHealthScore >= 80 ? 'text-green-600' : siteHealthScore >= 60 ? 'text-yellow-600' : siteHealthScore >= 40 ? 'text-orange-600' : 'text-red-600'}`}>
                            {siteHealthScore}
                          </span>
                        </div>
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-gray-800">Site Health Score</h3>
                        <p className="text-sm text-gray-500">
                          {siteHealthScore >= 80 ? 'Excellent! Few issues to address.' :
                           siteHealthScore >= 60 ? 'Good, but some issues need attention.' :
                           siteHealthScore >= 40 ? 'Needs work. Several issues to fix.' :
                           'Critical issues detected. Immediate attention needed.'}
                        </p>
                      </div>
                    </div>
                    {/* Issue Summary */}
                    <div className="flex gap-4">
                      <div className="text-center px-4 py-2 bg-red-50 rounded-lg border border-red-200">
                        <div className="text-2xl font-bold text-red-700">{issues.filter(i => i.severity === 'critical').length}</div>
                        <div className="text-xs text-red-600">Critical</div>
                      </div>
                      <div className="text-center px-4 py-2 bg-orange-50 rounded-lg border border-orange-200">
                        <div className="text-2xl font-bold text-orange-700">{issues.filter(i => i.severity === 'high').length}</div>
                        <div className="text-xs text-orange-600">High</div>
                      </div>
                      <div className="text-center px-4 py-2 bg-yellow-50 rounded-lg border border-yellow-200">
                        <div className="text-2xl font-bold text-yellow-700">{issues.filter(i => i.severity === 'medium').length}</div>
                        <div className="text-xs text-yellow-600">Medium</div>
                      </div>
                      <div className="text-center px-4 py-2 bg-blue-50 rounded-lg border border-blue-200">
                        <div className="text-2xl font-bold text-blue-700">{issues.filter(i => i.severity === 'low').length}</div>
                        <div className="text-xs text-blue-600">Low</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Filters Row */}
                <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
                  {/* Impact Filter Buttons */}
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => setIssueImpactFilter('all')}
                      className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                        issueImpactFilter === 'all'
                          ? 'bg-gray-800 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      All Issues ({aggregatedIssues.length})
                    </button>
                    <button
                      onClick={() => setIssueImpactFilter('seo')}
                      className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                        issueImpactFilter === 'seo'
                          ? 'bg-purple-600 text-white'
                          : 'bg-purple-50 text-purple-700 hover:bg-purple-100'
                      }`}
                    >
                      SEO Killers ({aggregatedIssues.filter(g => g.impact === 'seo').length})
                    </button>
                    <button
                      onClick={() => setIssueImpactFilter('ux')}
                      className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                        issueImpactFilter === 'ux'
                          ? 'bg-blue-600 text-white'
                          : 'bg-blue-50 text-blue-700 hover:bg-blue-100'
                      }`}
                    >
                      User Experience ({aggregatedIssues.filter(g => g.impact === 'ux').length})
                    </button>
                    <button
                      onClick={() => setIssueImpactFilter('compliance')}
                      className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                        issueImpactFilter === 'compliance'
                          ? 'bg-green-600 text-white'
                          : 'bg-green-50 text-green-700 hover:bg-green-100'
                      }`}
                    >
                      Compliance ({aggregatedIssues.filter(g => g.impact === 'compliance').length})
                    </button>
                    <button
                      onClick={() => setIssueImpactFilter('performance')}
                      className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                        issueImpactFilter === 'performance'
                          ? 'bg-orange-600 text-white'
                          : 'bg-orange-50 text-orange-700 hover:bg-orange-100'
                      }`}
                    >
                      Performance ({aggregatedIssues.filter(g => g.impact === 'performance').length})
                    </button>
                  </div>

                  {/* Export Button */}
                  <button
                    onClick={handleExportIssues}
                    className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                  >
                    <Download className="w-4 h-4" />
                    Export All Issues
                  </button>
                </div>

                {/* Issue Cards */}
                {filteredAggregatedIssues.length > 0 ? (
                  <div className="space-y-4">
                    {filteredAggregatedIssues.map((group) => {
                      const isExpanded = expandedIssueCards.has(group.key);
                      const description = getIssueDescription(group.message);
                      const severityColors = {
                        critical: { border: 'border-l-red-600', bg: 'bg-red-50', text: 'text-red-700', badge: 'bg-red-100 text-red-800' },
                        high: { border: 'border-l-orange-500', bg: 'bg-orange-50', text: 'text-orange-700', badge: 'bg-orange-100 text-orange-800' },
                        medium: { border: 'border-l-yellow-500', bg: 'bg-yellow-50', text: 'text-yellow-700', badge: 'bg-yellow-100 text-yellow-800' },
                        low: { border: 'border-l-blue-400', bg: 'bg-blue-50', text: 'text-blue-700', badge: 'bg-blue-100 text-blue-800' }
                      };
                      const colors = severityColors[group.severity];

                      return (
                        <div key={group.key} className={`border-l-4 ${colors.border} rounded-lg bg-white shadow-sm overflow-hidden`}>
                          {/* Card Header */}
                          <div
                            className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors`}
                            onClick={() => toggleIssueCard(group.key)}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center gap-3 mb-2">
                                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${colors.badge}`}>
                                    {group.severity.toUpperCase()}
                                  </span>
                                  <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded-full">
                                    {group.type}
                                  </span>
                                </div>
                                <h3 className="text-lg font-semibold text-gray-900 mb-1">{group.message}</h3>
                                <p className="text-sm text-gray-600">
                                  Found <span className="font-semibold">{group.count}</span> {group.count === 1 ? 'instance' : 'instances'} across <span className="font-semibold">{group.pageCount}</span> {group.pageCount === 1 ? 'page' : 'pages'}
                                </p>
                                {description && (
                                  <p className="mt-2 text-sm text-gray-500 italic">
                                    {description}
                                  </p>
                                )}
                              </div>
                              <div className="flex items-center gap-3">
                                <button
                                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                                >
                                  {isExpanded ? 'Hide Details' : 'View Details'}
                                </button>
                                {isExpanded ? (
                                  <ChevronUp className="w-5 h-5 text-gray-400" />
                                ) : (
                                  <ChevronDown className="w-5 h-5 text-gray-400" />
                                )}
                              </div>
                            </div>
                          </div>

                          {/* Accordion Content - Shows actual specific instances */}
                          {isExpanded && (() => {
                            const instanceData = getIssueInstances(group);
                            const maxItems = 25;
                            const displayItems = instanceData.items.slice(0, maxItems);

                            return (
                              <div className="border-t border-gray-200 bg-gray-50 p-4">
                                {displayItems.length > 0 ? (
                                  <div className="overflow-x-auto">
                                    <table className="min-w-full divide-y divide-gray-200 bg-white rounded-lg overflow-hidden">
                                      <thead className="bg-gray-100">
                                        <tr>
                                          {instanceData.columns.map((col) => (
                                            <th
                                              key={col.key}
                                              className="px-4 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase"
                                            >
                                              {col.label}
                                            </th>
                                          ))}
                                        </tr>
                                      </thead>
                                      <tbody className="divide-y divide-gray-200">
                                        {displayItems.map((item, idx) => (
                                          <tr key={item.id || idx} className="hover:bg-gray-50">
                                            {instanceData.columns.map((col) => (
                                              <td key={col.key} className="px-4 py-3">
                                                {col.render ? col.render(item) : item[col.key]}
                                              </td>
                                            ))}
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                    {instanceData.items.length > maxItems && (
                                      <div className="text-center py-3 text-sm text-gray-500">
                                        Showing {maxItems} of {instanceData.items.length} items. Export CSV for full list.
                                      </div>
                                    )}
                                  </div>
                                ) : (
                                  <div className="text-center py-6 text-sm text-gray-500">
                                    <Info className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                                    No specific instances found. This may be a summary-level issue.
                                  </div>
                                )}
                              </div>
                            );
                          })()}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-center py-12 bg-gray-50 rounded-xl border border-gray-200">
                    <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-800 mb-2">
                      {issues.length === 0 ? 'No Issues Found!' : 'No Matching Issues'}
                    </h3>
                    <p className="text-gray-500">
                      {issues.length === 0
                        ? 'Great job! This crawl found no issues to report.'
                        : 'Try adjusting your filters to see more issues.'}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Images Tab */}
            {activeTab === 'images' && (
              <div className="p-6">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-xl font-semibold text-gray-800">Images</h2>
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <label className="text-sm text-gray-600">Alt Text:</label>
                      <select
                        value={imageAltFilter}
                        onChange={(e) => setImageAltFilter(e.target.value as any)}
                        className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="all">All</option>
                        <option value="with_alt">With Alt Text</option>
                        <option value="missing_alt">Missing Alt Text</option>
                      </select>
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="text-sm text-gray-600">Status:</label>
                      <select
                        value={imageBrokenFilter}
                        onChange={(e) => setImageBrokenFilter(e.target.value as any)}
                        className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="all">All</option>
                        <option value="working">Working</option>
                        <option value="broken">Broken</option>
                      </select>
                    </div>
                    <button
                      onClick={handleExportImages}
                      className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                    >
                      <Download className="w-4 h-4" />
                      Export CSV
                    </button>
                  </div>
                </div>

                {images.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                            Image
                          </th>
                          <th
                            onClick={() => handleImageSort('src')}
                            className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase cursor-pointer hover:bg-gray-100 select-none"
                          >
                            Source URL <SortIcon column="src" currentSort={imageSort} currentDir={imageSortDir} />
                          </th>
                          <th
                            onClick={() => handleImageSort('alt')}
                            className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase cursor-pointer hover:bg-gray-100 select-none"
                          >
                            Alt Text <SortIcon column="alt" currentSort={imageSort} currentDir={imageSortDir} />
                          </th>
                          <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                            Dimensions
                          </th>
                          <th
                            onClick={() => handleImageSort('status')}
                            className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase cursor-pointer hover:bg-gray-100 select-none"
                          >
                            Status <SortIcon column="status" currentSort={imageSort} currentDir={imageSortDir} />
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {getSortedImages().map((image) => (
                          <tr key={image.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4">
                              <img
                                src={image.src}
                                alt={image.alt || 'Image'}
                                className="w-16 h-16 object-cover rounded"
                                onError={(e) => {
                                  e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Crect fill="%23ddd" width="100" height="100"/%3E%3Ctext fill="%23999" x="50%" y="50%" text-anchor="middle" dy=".3em"%3ENo Image%3C/text%3E%3C/svg%3E';
                                }}
                              />
                            </td>
                            <td className="px-6 py-4">
                              <a
                                href={image.src}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm text-secondary-600 hover:text-secondary-700 underline truncate max-w-xs block"
                                title={image.src}
                              >
                                {image.src}
                              </a>
                            </td>
                            <td className="px-6 py-4">
                              <div className="text-sm text-gray-900 max-w-xs truncate" title={image.alt}>
                                {image.has_alt ? (
                                  <span>{image.alt || 'Empty'}</span>
                                ) : (
                                  <span className="text-red-600">Missing</span>
                                )}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-gray-500">
                                {image.width && image.height ? `${image.width} × ${image.height}` : 'N/A'}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              {image.is_broken ? (
                                <span className="inline-flex px-2 py-1 text-xs font-semibold text-red-800 bg-red-100 rounded-full">
                                  Broken {image.status_code ? `(${image.status_code})` : ''}
                                </span>
                              ) : (
                                <span className="inline-flex px-2 py-1 text-xs font-semibold text-green-800 bg-green-100 rounded-full">
                                  OK {image.status_code ? `(${image.status_code})` : ''}
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="p-4 text-sm text-gray-700 bg-gray-100 rounded-md">
                    <p>No images found for this crawl.</p>
                  </div>
                )}
              </div>
            )}

          </>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Delete Crawl</h3>
              <p className="text-gray-600 mb-4">
                Are you sure you want to delete this crawl? This will permanently remove the crawl and all associated data including:
              </p>
              <ul className="list-disc list-inside text-sm text-gray-600 mb-6 space-y-1">
                <li>All crawled pages ({pages.length} page{pages.length !== 1 ? 's' : ''})</li>
                <li>All links</li>
                <li>All SEO metadata</li>
                <li>All issues</li>
                <li>All stored files</li>
              </ul>
              <p className="text-red-600 font-medium text-sm mb-6">
                This action cannot be undone.
              </p>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  disabled={deleting}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-secondary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDelete}
                  disabled={deleting}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {deleting ? 'Deleting...' : 'Delete Permanently'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Re-run Confirmation Modal */}
      <ConfirmationModal
        isOpen={showRerunConfirm}
        onClose={() => setShowRerunConfirm(false)}
        onConfirm={handleRerun}
        title="Re-run Crawl"
        message={`Are you sure you want to re-run this crawl? This will create a new crawl job with the same settings: "${crawl.name}".`}
        confirmText="Re-run Crawl"
        variant="info"
        isLoading={rerunning}
      />

      {/* Stop Crawl Confirmation Modal */}
      <ConfirmationModal
        isOpen={showStopConfirm}
        onClose={() => setShowStopConfirm(false)}
        onConfirm={handleStopCrawl}
        title="Stop Crawl"
        message={`Are you sure you want to stop this crawl? The crawl will be marked as stopped and any progress will be saved.`}
        confirmText="Stop Crawl"
        variant="warning"
        isLoading={stopping}
      />
    </div>
  );
};

export default CrawlDetailPage;
