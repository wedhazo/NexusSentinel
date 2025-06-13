import React, { useState, useEffect } from 'react';
import axios from 'axios';

// Types for news data
interface NewsItem {
  id: string;
  title: string;
  summary: string;
  url: string;
  source: string;
  publishedAt: string;
  category: string;
  sentimentScore: number;
  sentimentLabel: 'positive' | 'negative' | 'neutral';
  relatedSymbols: string[];
}

// Available news categories
const CATEGORIES = [
  'All',
  'Markets',
  'Economy',
  'Stocks',
  'Commodities',
  'Forex',
  'Crypto',
  'Technology',
  'Politics'
];

const NewsHeadlines: React.FC = () => {
  // State for news data
  const [news, setNews] = useState<NewsItem[]>([]);
  const [filteredNews, setFilteredNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filtering state
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Format date to readable format
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    
    // If the news is from today, show time only
    if (date.toDateString() === now.toDateString()) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    // If the news is from yesterday, show "Yesterday"
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    }
    
    // Otherwise show the date
    return date.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric'
    });
  };

  // Get sentiment color based on score
  const getSentimentColor = (score: number): string => {
    if (score >= 0.3) return 'bg-green-100 text-green-800 border-green-200';
    if (score <= -0.3) return 'bg-red-100 text-red-800 border-red-200';
    return 'bg-gray-100 text-gray-800 border-gray-200';
  };

  // Get sentiment icon based on label
  const getSentimentIcon = (label: string): JSX.Element => {
    if (label === 'positive') {
      return (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
      );
    }
    if (label === 'negative') {
      return (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
      );
    }
    return (
      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
      </svg>
    );
  };

  // Fetch news data
  useEffect(() => {
    const fetchNews = async () => {
      try {
        setLoading(true);
        
        // In a real implementation, you would fetch from your API:
        // const response = await axios.get(`${import.meta.env.VITE_API_URL}/api/v1/news/headlines`);
        // setNews(response.data);
        
        // Mock data for development
        const mockNews: NewsItem[] = [
          {
            id: '1',
            title: 'Fed Signals Potential Rate Cut in September Meeting',
            summary: 'Federal Reserve officials indicated they could cut interest rates at their September meeting if inflation continues to cool.',
            url: 'https://example.com/news/1',
            source: 'Financial Times',
            publishedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
            category: 'Economy',
            sentimentScore: 0.65,
            sentimentLabel: 'positive',
            relatedSymbols: ['SPY', 'QQQ', 'DIA']
          },
          {
            id: '2',
            title: 'Apple Announces New AI Features for iOS 19',
            summary: 'Apple unveiled a suite of new AI features coming to iPhones later this year, including enhanced Siri capabilities.',
            url: 'https://example.com/news/2',
            source: 'TechCrunch',
            publishedAt: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(), // 4 hours ago
            category: 'Technology',
            sentimentScore: 0.78,
            sentimentLabel: 'positive',
            relatedSymbols: ['AAPL', 'MSFT', 'GOOGL']
          },
          {
            id: '3',
            title: 'Oil Prices Fall on Increased Supply Concerns',
            summary: 'Crude oil prices dropped over 3% as OPEC+ countries discuss increasing production quotas.',
            url: 'https://example.com/news/3',
            source: 'Reuters',
            publishedAt: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(), // 6 hours ago
            category: 'Commodities',
            sentimentScore: -0.45,
            sentimentLabel: 'negative',
            relatedSymbols: ['CL=F', 'USO', 'XOM', 'CVX']
          },
          {
            id: '4',
            title: 'Tesla Misses Delivery Expectations, Stock Down 5%',
            summary: 'Tesla reported quarterly vehicle deliveries below analyst expectations, citing supply chain challenges.',
            url: 'https://example.com/news/4',
            source: 'CNBC',
            publishedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
            category: 'Stocks',
            sentimentScore: -0.62,
            sentimentLabel: 'negative',
            relatedSymbols: ['TSLA']
          },
          {
            id: '5',
            title: 'Bitcoin Stabilizes Above $60,000 After Recent Volatility',
            summary: 'The world\'s largest cryptocurrency has found support above the $60,000 level after last week\'s sell-off.',
            url: 'https://example.com/news/5',
            source: 'CoinDesk',
            publishedAt: new Date(Date.now() - 1.5 * 24 * 60 * 60 * 1000).toISOString(), // 1.5 days ago
            category: 'Crypto',
            sentimentScore: 0.12,
            sentimentLabel: 'neutral',
            relatedSymbols: ['BTC-USD', 'COIN', 'MSTR']
          },
          {
            id: '6',
            title: 'Dollar Weakens Against Major Currencies on Rate Cut Expectations',
            summary: 'The U.S. dollar index fell to a three-month low as markets price in potential Fed rate cuts.',
            url: 'https://example.com/news/6',
            source: 'Bloomberg',
            publishedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), // 2 days ago
            category: 'Forex',
            sentimentScore: -0.25,
            sentimentLabel: 'neutral',
            relatedSymbols: ['DXY', 'UUP', 'FXE']
          },
          {
            id: '7',
            title: 'Amazon Expands Healthcare Initiative with New Acquisitions',
            summary: 'Amazon announced two healthcare acquisitions as part of its strategy to disrupt the healthcare industry.',
            url: 'https://example.com/news/7',
            source: 'Wall Street Journal',
            publishedAt: new Date(Date.now() - 2.5 * 24 * 60 * 60 * 1000).toISOString(), // 2.5 days ago
            category: 'Stocks',
            sentimentScore: 0.58,
            sentimentLabel: 'positive',
            relatedSymbols: ['AMZN', 'CVS', 'WBA']
          },
          {
            id: '8',
            title: 'SEC Approves New ESG Disclosure Rules for Public Companies',
            summary: 'The Securities and Exchange Commission voted to require standardized climate-related disclosures from public companies.',
            url: 'https://example.com/news/8',
            source: 'Financial Times',
            publishedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(), // 3 days ago
            category: 'Politics',
            sentimentScore: 0.05,
            sentimentLabel: 'neutral',
            relatedSymbols: ['XLF', 'ESGU', 'SPYX']
          }
        ];
        
        setNews(mockNews);
        setFilteredNews(mockNews);
        setError(null);
      } catch (err) {
        console.error('Error fetching news:', err);
        setError('Failed to load news headlines. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchNews();
  }, []);

  // Filter news when category or search changes
  useEffect(() => {
    let filtered = [...news];
    
    // Filter by category
    if (selectedCategory !== 'All') {
      filtered = filtered.filter(item => item.category === selectedCategory);
    }
    
    // Filter by search query
    if (searchQuery.trim() !== '') {
      const query = searchQuery.toLowerCase().trim();
      filtered = filtered.filter(
        item => 
          item.title.toLowerCase().includes(query) || 
          item.summary.toLowerCase().includes(query) ||
          item.relatedSymbols.some(symbol => symbol.toLowerCase().includes(query))
      );
    }
    
    setFilteredNews(filtered);
  }, [selectedCategory, searchQuery, news]);

  // Render loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-4 text-gray-600">Loading news headlines...</p>
        </div>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <svg 
          className="w-12 h-12 text-red-500 mx-auto mb-4" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24" 
          xmlns="http://www.w3.org/2000/svg"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth="2" 
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <h3 className="text-lg font-medium text-red-800 mb-2">Error</h3>
        <p className="text-red-600">{error}</p>
        <button 
          onClick={() => window.location.reload()} 
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Market News Headlines</h2>
      
      {/* Search and Filter Controls */}
      <div className="flex flex-col md:flex-row justify-between mb-6 space-y-4 md:space-y-0">
        <div className="relative w-full md:w-1/2 mr-0 md:mr-4">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            placeholder="Search headlines, symbols..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        
        <div className="flex overflow-x-auto pb-2 md:pb-0 -mx-2 md:mx-0">
          {CATEGORIES.map(category => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`mx-1 px-3 py-1 rounded-full text-sm font-medium whitespace-nowrap ${
                selectedCategory === category
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {category}
            </button>
          ))}
        </div>
      </div>
      
      {/* News List */}
      {filteredNews.length === 0 ? (
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No news found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Try changing your search or filter criteria.
          </p>
          <div className="mt-6">
            <button
              onClick={() => {
                setSelectedCategory('All');
                setSearchQuery('');
              }}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Reset filters
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {filteredNews.map((item) => (
            <div key={item.id} className="border-b border-gray-200 pb-6 last:border-b-0 last:pb-0">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-1">
                    <span className="text-sm font-medium text-gray-500">{item.source}</span>
                    <span className="text-sm text-gray-400">•</span>
                    <span className="text-sm text-gray-500">{formatDate(item.publishedAt)}</span>
                    <span className="text-sm text-gray-400">•</span>
                    <span className="text-sm text-gray-500">{item.category}</span>
                  </div>
                  
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    <a href={item.url} target="_blank" rel="noopener noreferrer" className="hover:text-blue-600">
                      {item.title}
                    </a>
                  </h3>
                  
                  <p className="text-gray-600 mb-3">{item.summary}</p>
                  
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getSentimentColor(item.sentimentScore)}`}>
                      {getSentimentIcon(item.sentimentLabel)}
                      <span className="ml-1">
                        {item.sentimentLabel.charAt(0).toUpperCase() + item.sentimentLabel.slice(1)} ({item.sentimentScore.toFixed(2)})
                      </span>
                    </span>
                    
                    {item.relatedSymbols.map(symbol => (
                      <span key={symbol} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">
                        {symbol}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* View More Button */}
      {filteredNews.length > 0 && (
        <div className="mt-6 text-center">
          <button
            className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            View more news
            <svg className="ml-2 -mr-1 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
};

export default NewsHeadlines;
