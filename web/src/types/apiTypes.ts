/**
 * API Types for NexusSentinel
 * 
 * This file contains TypeScript interfaces for the API responses from the backend endpoints.
 * These types ensure proper typing in the frontend components when making API calls.
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
  isin?: string;
  ceo?: string;
  website?: string;
  business_summary?: string;
  number_of_employees?: number;
  fiscal_year_end?: string;
  ipo_date?: string;
}

export interface StockCoreResponse extends StockCore {
  stock_id: number;
  created_at: string;
  last_updated: string;
  is_active: number;
}

// Sentiment Analysis Types
export interface SentimentAnalysisCreate {
  symbol: string;
  date: string;
  source: string;
  sentiment_score: number;
  sentiment_label: string;
  volume: number;
  content_sample?: string;
  source_details?: Record<string, any>;
}

export interface SentimentAnalysisResponse {
  id: number;
  stock_id: number;
  symbol: string;
  date: string;
  source: string;
  sentiment_score: number;
  sentiment_label: string;
  volume: number;
  created_at: string;
}

export interface SentimentDistribution {
  positive: number;
  neutral: number;
  negative: number;
}

export interface AggregatedSentimentResponse {
  symbol: string;
  date: string;
  source: string;
  avg_sentiment_score: number;
  total_volume: number;
  sentiment_distribution: SentimentDistribution;
}

// Top/Bottom Sentiment Types
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

export interface MarketOverviewResponse {
  indices: MarketIndex[];
  historical: HistoricalDataPoint[];
  volatility?: {
    value: number;
    change: number;
    level: string;
  };
  trading_volume?: {
    value: number;
    change_percent: number;
  };
  advancing_stocks?: {
    percent: number;
    trend: string;
  };
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

// --------------------------------------------------
// Watchlist Types
// --------------------------------------------------

// Payload for adding a symbol to the watchlist
export interface WatchlistCreate {
  symbol: string;
}

// Item returned from the watchlist endpoints
export interface WatchlistItem {
  id: number;
  symbol: string;
  company_name: string;
  date_added: string;
  sentiment_score?: number;
}

// Response from `GET /watchlist`
export type WatchlistResponse = WatchlistItem[];

// Full Stock Data Response
export interface StockFullDataResponse {
  // Core stock data
  stock_id: number;
  symbol: string;
  company_name: string;
  exchange?: string;
  sector?: string;
  industry?: string;
  country_of_origin?: string;
  cik?: string;
  isin?: string;
  ceo?: string;
  website?: string;
  business_summary?: string;
  number_of_employees?: number;
  fiscal_year_end?: string;
  ipo_date?: string;
  core_last_updated?: string;
  
  // Daily OHLCV data
  daily_open?: number;
  daily_high?: number;
  daily_low?: number;
  daily_close?: number;
  daily_adjusted_close?: number;
  daily_volume?: number;
  
  // Intraday data
  intraday_timestamp?: string;
  intraday_open?: number;
  intraday_high?: number;
  intraday_low?: number;
  intraday_close?: number;
  intraday_volume?: number;
  
  // Financial data
  q_report_date?: string;
  q_period_end_date?: string;
  q_fiscal_year?: number;
  q_fiscal_quarter?: number;
  q_revenue?: number;
  q_net_income?: number;
  q_eps_basic?: number;
  q_ebitda?: number;
  q_free_cash_flow?: number;
  
  a_report_date?: string;
  a_fiscal_year?: number;
  a_revenue?: number;
  a_net_income?: number;
  a_eps_basic?: number;
  a_ebitda?: number;
  a_free_cash_flow?: number;
  
  // Technical indicators
  sma_5?: number;
  sma_10?: number;
  sma_20?: number;
  sma_50?: number;
  sma_100?: number;
  sma_200?: number;
  ema_10?: number;
  ema_20?: number;
  ema_50?: number;
  ema_100?: number;
  ema_200?: number;
  macd?: number;
  macd_signal?: number;
  macd_hist?: number;
  rsi_14?: number;
  rsi_20?: number;
  bbands_upper?: number;
  bbands_middle?: number;
  bbands_lower?: number;
  atr_14?: number;
  adx_14?: number;
  obv?: number;
  vwap?: number;
  stochastic_k?: number;
  stochastic_d?: number;
  cci_14?: number;
  
  // Latest news
  latest_news_title?: string;
  latest_news_url?: string;
  latest_news_published_at?: string;
  latest_news_sentiment?: number;
  latest_news_sentiment_label?: string;
  
  // Latest social post
  latest_social_post_text?: string;
  latest_social_platform?: string;
  latest_social_created_at?: string;
  latest_social_sentiment?: number;
  
  // Sentiment summary
  news_avg_sentiment?: number;
  news_volume_24h?: number;
  twitter_avg_sentiment?: number;
  twitter_mentions_24h?: number;
  reddit_avg_sentiment?: number;
  reddit_mentions_24h?: number;
  wallstreetbets_mentions_24h?: number;
  overall_sentiment_score?: number;
  sentiment_trend?: string;
  
  // Latest dividend
  latest_dividend_ex_date?: string;
  latest_dividend_amount?: number;
  latest_dividend_type?: string;
  
  // Latest split
  latest_split_ex_date?: string;
  latest_split_from_shares?: number;
  latest_split_to_shares?: number;
  
  // Latest analyst rating
  latest_rating_report_date?: string;
  latest_rating_firm?: string;
  latest_rating?: string;
  latest_rating_target_price?: number;
  
  // Macro economic data
  macro_value?: number;
  macro_indicator_name?: string;
  macro_indicator_unit?: string;
}

// API Error Response
export interface ApiError {
  message: string;
  status?: number;
  errors?: Record<string, any>;
}
