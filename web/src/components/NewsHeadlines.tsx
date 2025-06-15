import React, { useState, useEffect } from 'react';
import { api } from '../api/apiClient';
import { NewsItem, NewsResponse } from '../types/apiTypes';

const NewsHeadlines: React.FC = () => {
  // State for news data
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);

  // Fetch news data
  useEffect(() => {
    const fetchNews = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch data from backend API
        const response = await api.get<NewsResponse>(`/news?page=${page}&page_size=5`);
        
        setNews(response.news);
        setTotalPages(Math.ceil(response.total / response.page_size));
      } catch (err: any) {
        console.error('Error fetching news:', err);
        setError(err.message || 'Failed to load news. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchNews();
  }, [page]);

  // Format date for display
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  // Get sentiment badge color and text
  const getSentimentBadge = (score?: number, label?: string) => {
    if (score === undefined || label === undefined) {
      return { color: 'bg-gray-100 text-gray-800', text: 'Neutral' };
    }
    
    if (score > 0.3) {
      return { color: 'bg-green-100 text-green-800', text: 'Positive' };
    } else if (score > -0.3) {
      return { color: 'bg-gray-100 text-gray-800', text: label || 'Neutral' };
    } else {
      return { color: 'bg-red-100 text-red-800', text: 'Negative' };
    }
  };

  // Handle page change
  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setPage(newPage);
    }
  };

  // Render loading state
  if (loading && news.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Market News</h2>
        <div className="flex items-center justify-center min-h-[200px]">
          <div className="flex flex-col items-center">
            <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <p className="mt-4 text-gray-600">Loading news...</p>
          </div>
        </div>
      </div>
    );
  }

  // Render error state
  if (error && news.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Market News</h2>
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
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Market News</h2>
      
      {/* News List */}
      <div className="space-y-6">
        {news.map((item) => {
          const sentimentBadge = getSentimentBadge(item.sentiment_score, item.sentiment_label);
          
          return (
            <div key={item.id} className="border-b border-gray-200 pb-6 last:border-0 last:pb-0">
              <div className="flex justify-between items-start">
                <h3 className="text-lg font-semibold text-gray-800 hover:text-blue-600 transition-colors">
                  <a href={item.url} target="_blank" rel="noopener noreferrer">
                    {item.title}
                  </a>
                </h3>
                <span className={`${sentimentBadge.color} text-xs font-medium px-2.5 py-0.5 rounded-full ml-2`}>
                  {sentimentBadge.text}
                </span>
              </div>
              
              <div className="flex items-center mt-2 text-sm text-gray-500">
                <span className="font-medium">{item.source}</span>
                <span className="mx-2">•</span>
                <span>{formatDate(item.published_at)}</span>
                {item.symbol && (
                  <>
                    <span className="mx-2">•</span>
                    <span className="font-mono bg-gray-100 px-1.5 py-0.5 rounded">
                      {item.symbol}
                    </span>
                  </>
                )}
              </div>
            </div>
          );
        })}
        
        {news.length === 0 && !loading && (
          <div className="text-center py-8 text-gray-500">
            <svg 
              className="w-16 h-16 text-gray-300 mx-auto mb-4" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24" 
              xmlns="http://www.w3.org/2000/svg"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth="2" 
                d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"
              />
            </svg>
            <p>No news articles found</p>
          </div>
        )}
      </div>
      
      {/* Loading indicator for pagination */}
      {loading && news.length > 0 && (
        <div className="flex justify-center my-6">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
      )}
      
      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center space-x-2 mt-6">
          <button 
            onClick={() => handlePageChange(page - 1)}
            disabled={page === 1 || loading}
            className={`px-3 py-1 rounded-md text-sm font-medium ${
              page === 1 || loading
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Previous
          </button>
          
          <span className="text-sm text-gray-600">
            Page {page} of {totalPages}
          </span>
          
          <button 
            onClick={() => handlePageChange(page + 1)}
            disabled={page === totalPages || loading}
            className={`px-3 py-1 rounded-md text-sm font-medium ${
              page === totalPages || loading
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default NewsHeadlines;
