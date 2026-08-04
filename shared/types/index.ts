export interface User {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string;
  role: 'admin' | 'owner' | 'member' | 'user';
  is_verified: boolean;
  two_factor_enabled: boolean;
  credits_balance: number;
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  type: 'document' | 'website' | 'bot' | 'code' | 'general';
  is_archived: boolean;
  user_id: string;
  organization_id?: string;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: string;
  title: string;
  content?: string;
  humanized_content?: string;
  content_type: 'txt' | 'markdown' | 'docx' | 'pdf' | 'rtf';
  tone?: string;
  audience?: string;
  readability_score?: number;
  original_ai_score?: number;
  humanized_ai_score?: number;
  word_count?: number;
  language: string;
  project_id?: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface Website {
  id: string;
  name: string;
  template_id?: string;
  framework: 'html-css' | 'react' | 'nextjs' | 'vue' | 'angular' | 'svelte';
  styling: 'tailwind' | 'bootstrap' | 'plain-css';
  pages?: any;
  theme_config?: any;
  preview_url?: string;
  published_url?: string;
  deployment_status: 'draft' | 'building' | 'deployed' | 'failed';
  is_published: boolean;
  project_id?: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface WebsiteTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  frameworks: string[];
}

export interface Bot {
  id: string;
  name: string;
  description?: string;
  system_prompt?: string;
  model: string;
  temperature: number;
  is_active: boolean;
  deployment_url?: string;
  project_id?: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface ChatSession {
  id: string;
  title: string;
  model: string;
  system_prompt?: string;
  is_archived: boolean;
  user_id: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  tokens_used?: number;
  latency_ms?: number;
  created_at: string;
}

export interface CodeProject {
  id: string;
  name: string;
  description?: string;
  language: string;
  framework?: string;
  files?: any;
  project_id?: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  created_at: string;
  last_used_at?: string;
  is_active: boolean;
}

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  category: string;
  title: string;
  body?: string;
  link?: string;
  is_read: boolean;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}
