import axios, { AxiosInstance } from 'axios';
import { supabase } from '../lib/supabase';

// Types
export interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  last_sign_in_at?: string;
  last_login?: string;
  full_name?: string;
  user_metadata?: {
    full_name?: string;
    is_admin?: boolean;
  };
}

export interface UserCreate {
  email: string;
  password: string;
  full_name: string;
  is_admin: boolean;
}

export interface Crawl {
  id: string;
  user_id: string;
  url: string;
  name: string;
  status: 'pending' | 'queued' | 'running' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
  max_depth: number;
  max_pages: number;
  respect_robots_txt: boolean;
  follow_external_links: boolean;
  js_rendering: boolean;
  rate_limit: number;
  user_agent?: string;
  created_at: string;
  updated_at: string;
  error?: string;
  task_id?: string;
}

export interface CrawlCreate {
  url: string;
  name: string;
  max_depth: number;
  max_pages: number;
  respect_robots_txt: boolean;
  follow_external_links: boolean;
  js_rendering: boolean;
  rate_limit: number;
  user_agent?: string;
}

export interface Page {
  id: string;
  crawl_id: string;
  url: string;
  title: string;
  status_code: number;
  content_type: string;
  load_time_ms: number;
  html_snapshot_path?: string;
  screenshot_path?: string;
  crawl_depth: number;
  created_at: string;
}

export interface Link {
  id: string;
  crawl_id: string;
  source_url: string;
  target_url: string;
  anchor_text: string;
  is_internal: boolean;
  is_broken: boolean;
  status_code?: number;
  created_at: string;
}

export interface Issue {
  id: string;
  crawl_id: string;
  url: string;
  issue_type: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
  created_at: string;
}

export interface Image {
  id: string;
  crawl_id: string;
  page_id: string;
  src: string;
  alt?: string;
  title?: string;
  width?: number;
  height?: number;
  has_alt: boolean;
  is_broken: boolean;
  status_code?: number;
  error?: string;
  created_at: string;
}

// API class
class ApiService {
  private api: AxiosInstance;
  
  constructor() {
    this.api = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    // Add auth token to requests
    this.api.interceptors.request.use(async (config) => {
      try {
        const { data: { session }, error } = await supabase.auth.getSession();
        
        console.log('Auth interceptor - session check:', {
          hasSession: !!session,
          hasUser: !!session?.user,
          hasToken: !!session?.access_token,
          error: error?.message
        });
        
        if (error) {
          console.error('Error getting session:', error);
          return config;
        }
        
        const token = session?.access_token;
        
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
          console.log('✅ Auth token added to request:', token.substring(0, 20) + '...');
        } else {
          console.warn('❌ No auth token available - user may not be logged in');
          console.log('Session details:', session);
        }
      } catch (error) {
        console.error('Error in auth interceptor:', error);
      }
      
      return config;
    });

    // Handle 401 errors by logging out
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          console.error('401 Unauthorized - clearing session and redirecting to login');
          await supabase.auth.signOut();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }
  
  // User endpoints
  async getCurrentUser(): Promise<User> {
    const response = await this.api.get('/users/me');
    return response.data;
  }
  
  async getUsers(): Promise<User[]> {
    const response = await this.api.get('/users');
    return response.data;
  }
  
  async createUser(userData: { email: string; password: string; full_name: string; is_admin: boolean }): Promise<User> {
    const response = await this.api.post('/users', userData);
    return response.data;
  }
  
  async deleteUser(id: string): Promise<{ message: string }> {
    const response = await this.api.delete(`/users/${id}`);
    return response.data;
  }
  
  async updateUserProfile(profileData: { full_name: string }): Promise<User> {
    const response = await this.api.patch('/users/me/profile', profileData);
    return response.data;
  }
  
  async updateUserPassword(passwordData: { current_password: string; new_password: string }): Promise<{ message: string }> {
    const response = await this.api.post('/users/me/change-password', passwordData);
    return response.data;
  }
  
  // Crawl endpoints
  async createCrawl(crawl: CrawlCreate): Promise<Crawl> {
    const response = await this.api.post('/crawls', crawl);
    return response.data;
  }
  
  async getCrawls(params?: { status?: string }): Promise<Crawl[]> {
    const response = await this.api.get('/crawls', { params });
    return response.data;
  }
  
  async getCrawl(id: string): Promise<Crawl> {
    const response = await this.api.get(`/crawls/${id}`);
    return response.data;
  }
  
  async deleteCrawl(id: string): Promise<{ message: string }> {
    const response = await this.api.delete(`/crawls/${id}`);
    return response.data;
  }

  async markCrawlFailed(id: string): Promise<{ message: string; crawl_id: string }> {
    const response = await this.api.post(`/crawls/${id}/mark-failed`);
    return response.data;
  }
  
  async getCrawlPages(id: string, params?: { skip?: number; limit?: number }): Promise<Page[]> {
    const response = await this.api.get(`/crawls/${id}/pages`, { params });
    return response.data;
  }

  async getPageDetail(crawlId: string, pageId: string): Promise<any> {
    const response = await this.api.get(`/crawls/${crawlId}/pages/${pageId}`);
    return response.data;
  }

  async getCrawlLinks(id: string, params?: { 
    skip?: number; 
    limit?: number;
    is_broken?: boolean;
    is_internal?: boolean;
  }): Promise<Link[]> {
    const response = await this.api.get(`/crawls/${id}/links`, { params });
    return response.data;
  }
  
  async getCrawlIssues(id: string, params?: {
    skip?: number;
    limit?: number;
    severity?: string;
  }): Promise<Issue[]> {
    const response = await this.api.get(`/crawls/${id}/issues`, { params });
    return response.data;
  }

  async getCrawlImages(id: string, params?: {
    skip?: number;
    limit?: number;
    is_broken?: boolean;
    has_alt?: boolean;
  }): Promise<Image[]> {
    const response = await this.api.get(`/crawls/${id}/images`, { params });
    return response.data;
  }

  async getCrawlAudit(id: string): Promise<any> {
    const response = await this.api.get(`/crawls/${id}/audit`);
    return response.data;
  }
  
  async getCrawlSummary(id: string): Promise<any> {
    const response = await this.api.get(`/crawls/${id}/summary`);
    return response.data;
  }
  
  async getPageHtml(crawlId: string, pageId: string): Promise<{ html_content: string }> {
    const response = await this.api.get(`/crawls/${crawlId}/html/${pageId}`);
    return response.data;
  }
  
  async getPageScreenshot(crawlId: string, pageId: string): Promise<{ screenshot_path: string }> {
    const response = await this.api.get(`/crawls/${crawlId}/screenshot/${pageId}`);
    return response.data;
  }
}

// Create and export a singleton instance
export const apiService = new ApiService();
