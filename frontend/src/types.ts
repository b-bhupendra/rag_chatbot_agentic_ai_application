export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  route?: 'faq' | 'sql' | 'fallback' | 'system';
  elapsedSeconds?: number;
  timestamp?: string;
}

export interface ChatResponse {
  response: string;
  route: 'faq' | 'sql' | 'fallback';
  elapsed_seconds: number;
  timestamp: string;
}

export interface HealthInfo {
  status: string;
  model: string;
  faq_count: number;
  product_count: number;
  chroma_dir: string;
  sqlite_path: string;
}

export interface SuggestionItem {
  text: string;
  category: string;
}
