export const TONES = {
  ACADEMIC: 'academic',
  PROFESSIONAL: 'professional',
  CASUAL: 'casual',
  FORMAL: 'formal',
  FRIENDLY: 'friendly',
  PERSUASIVE: 'persuasive',
  SIMPLE: 'simple',
  TECHNICAL: 'technical',
  NARRATIVE: 'narrative',
} as const;

export const DOCUMENT_TYPES = ['txt', 'markdown', 'docx', 'pdf', 'rtf'] as const;

export const WEBSITE_FRAMEWORKS = ['html-css', 'react', 'nextjs', 'vue', 'angular', 'svelte'] as const;

export const WEBSITE_STYLING = ['tailwind', 'bootstrap', 'plain-css'] as const;

export const BOT_CHANNELS = ['web', 'api', 'whatsapp', 'telegram', 'discord', 'slack'] as const;

export const PROJECT_TYPES = ['document', 'website', 'bot', 'code', 'general'] as const;

export const AI_MODELS = [
  { id: 'gpt-4o', name: 'GPT-4o', provider: 'openai' },
  { id: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'openai' },
  { id: 'claude-3-5-sonnet-20241022', name: 'Claude 3.5 Sonnet', provider: 'anthropic' },
  { id: 'claude-3-haiku-20240307', name: 'Claude 3 Haiku', provider: 'anthropic' },
  { id: 'llama3', name: 'Llama 3 (Local)', provider: 'ollama' },
] as const;

export const COLORS = {
  PRIMARY: '#2563EB',
  SECONDARY: '#7C3AED',
  ACCENT: '#06B6D4',
  SUCCESS: '#22C55E',
  WARNING: '#F59E0B',
  ERROR: '#EF4444',
  BG_LIGHT: '#F8FAFC',
  BG_DARK: '#0F172A',
  TEXT: '#111827',
} as const;
