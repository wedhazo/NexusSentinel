/**
 * API Types for NexusSentinel
 * 
 * This file contains TypeScript interfaces for the API responses from the backend endpoints.
 */

// Stock Core Data Types
export interface StockCore {
  symbol: string;
  company_name: string;
  exchange?: string;
  sector?: string;
  industry?: string;
  country_of_origin?: string;
  cik?: string;
  website?: string;
  business_summary?: string;
}

// Sentiment Analysis Types
export interface StockSentimentItem {
  symbol: string;
  sentiment_score: number;
  date: string;
}

export interface TopBottomStocksResponse {
  top_20: StockSentimentItem[];
  bottom_20: StockSentimentItem[];
}

// Market Overview Types
export interface MarketIndex {
  name: string;
  symbol: string;
  currentValue: number;
  change: number;
  changePercent: number;
  color?: string;
}

export interface HistoricalDataPoint {
  date: string;
  sp500: number;
  nasdaq: number;
  dowJones: number;
}

// News Types
export interface NewsItem {
  id: number;
  stock_id?: number;
  symbol?: string;
  title: string;
  url: string;
  source: string;
  author?: string;
  published_at: string;
  content?: string;
  sentiment_score?: number;
  sentiment_label?: string;
}

export interface NewsResponse {
  news: NewsItem[];
  total: number;
  page: number;
  page_size: number;
}

// Stock Search Types
export interface StockSearchResult {
  symbol: string;
  company_name: string;
  exchange?: string;
  current_price?: number;
  price_change_percent?: number;
  sentiment_score?: number;
}

export interface StockSearchResponse {
  results: StockSearchResult[];
  total: number;
}

// API Error Response
export interface ApiError {
  message: string;
  status?: number;
  errors?: Record<string, any>;
}
