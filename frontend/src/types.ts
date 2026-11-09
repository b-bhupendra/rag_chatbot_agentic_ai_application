export interface Product {
  product_link?: string;
  title?: string;
  brand?: string;
  price?: number;
  discount?: number;
  avg_rating?: number;
  total_ratings?: number;
  image_url?: string;
  [key: string]: any;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  route?: 'faq' | 'sql' | 'fallback' | 'system';
  elapsedSeconds?: number;
  timestamp?: string;
  products?: Product[];
  sqlQuery?: string;
}

export interface ChatResponse {
  response: string;
  route: 'faq' | 'sql' | 'fallback';
  elapsed_seconds: number;
  timestamp: string;
  products?: Product[];
  sql_query?: string;
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

