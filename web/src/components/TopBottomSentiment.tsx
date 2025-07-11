import React, { useState, useEffect } from 'react';
import { api } from '../api/apiClient';
import { TopBottomStocksResponse, StockSentimentItem } from '../types/apiTypes';

const TopBottomSentiment: React.FC = () => {
  // State variables
  const [sentimentData, setSentimentData] = useState<TopBottomStocksResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [queryDate, setQueryDate] = useState<string>(new Date().toISOString().split('T')[0]);

  // Fetch data when component mounts or query date changes
  useEffect(() => {
    const fetchSentimentData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch data from API
        const response = await api.get<TopBottomStocksResponse>(`/stocks/top-bottom-20?query_date=${queryDate}`);
        
        setSentimentData(response);
      } catch (err: any) {
        console.error('Error fetching sentiment data:', err);
        setError(err.message || 'Failed to load sentiment data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchSentimentData();
  }, [queryDate]);

  // Format sentiment score for display
  const formatSentiment = (score: number): string => {
    return score.toFixed(2);
  };

  // Get CSS class based on sentiment score
  const getSentimentClass = (score: number): string => {
    if (score > 0.3) return 'text-green-600 font-medium';
    if (score > 0) return 'text-green-500';
    if (score > -0.3) return 'text-red-500';
    return 'text-red-600 font-medium';
  };

  // Get background CSS class based on sentiment score
  const getBackgroundClass = (score: number, index: number): string => {
    const baseClass = 'border-l-4 pl-2 mb-2 flex justify-between items-center p-2 rounded-md';
    const alternatingBg = index % 2 === 0 ? 'bg-gray-50' : 'bg-white';
    
    if (score > 0.3) return `${baseClass} ${alternatingBg} border-green-600`;
    if (score > 0) return `${baseClass} ${alternatingBg} border-green-400`;
    if (score > -0.3) return `${baseClass} ${alternatingBg} border-red-400`;
    return `${baseClass} ${alternatingBg} border-red-600`;
  };

  // Render stock item
  const renderStockItem = (stock: StockSentimentItem, index: number) => {
    return (
      <div 
        key={stock.symbol} 
        className={getBackgroundClass(stock.sentiment_score, index)}
      >
        <div className="flex items-center">
          <span className="text-lg font-bold text-gray-800">{stock.symbol}</span>
          <span className="ml-2 text-xs text-gray-500">
            {new Date(stock.date).toLocaleDateString()}
          </span>
        </div>
        <div className={`text-right ${getSentimentClass(stock.sentiment_score)}`}>
          {stock.sentiment_score > 0 ? '+' : ''}{formatSentiment(stock.sentiment_score)}
        </div>
      </div>
    );
  };

  // Render loading state
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Market Sentiment</h2>
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="flex flex-col items-center">
            <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <p className="mt-4 text-gray-600">Loading sentiment data...</p>
          </div>
        </div>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Market Sentiment</h2>
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
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Market Sentiment</h2>
        <div className="flex items-center">
          <span className="text-sm text-gray-500 mr-2">Date:</span>
          <input
            type="date"
            value={queryDate}
            onChange={(e) => setQueryDate(e.target.value)}
            className="border border-gray-300 rounded-md px-2 py-1 text-sm"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Top Sentiment Stocks */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
            <svg className="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
              <path fillRule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clipRule="evenodd" />
            </svg>
            Top Sentiment
          </h3>
          <div className="border border-gray-200 rounded-lg p-3 bg-gray-50">
            {sentimentData?.top_20 && sentimentData.top_20.length > 0 ? (
              sentimentData.top_20.map((stock, index) => renderStockItem(stock, index))
            ) : (
              <p className="text-gray-500 text-center py-4">No data available</p>
            )}
          </div>
        </div>

        {/* Bottom Sentiment Stocks */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
            <svg className="w-5 h-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
              <path fillRule="evenodd" d="M12 13a1 1 0 110 2h-5a1 1 0 01-1-1v-5a1 1 0 112 0v3.586l4.293-4.293a1 1 0 011.414 0L16 10.586l4.293-4.293a1 1 0 111.414 1.414l-5 5a1 1 0 01-1.414 0L13 9.414 9.414 13H12z" clipRule="evenodd" />
            </svg>
            Bottom Sentiment
          </h3>
          <div className="border border-gray-200 rounded-lg p-3 bg-gray-50">
            {sentimentData?.bottom_20 && sentimentData.bottom_20.length > 0 ? (
              sentimentData.bottom_20.map((stock, index) => renderStockItem(stock, index))
            ) : (
              <p className="text-gray-500 text-center py-4">No data available</p>
            )}
          </div>
        </div>
      </div>

      <div className="mt-6 text-center">
        <p className="text-sm text-gray-500">
          Sentiment scores range from -1.0 (extremely negative) to 1.0 (extremely positive)
        </p>
      </div>
    </div>
  );
};

export default TopBottomSentiment;
