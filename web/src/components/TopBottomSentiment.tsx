import React, { useState, useEffect } from 'react';
import axios from 'axios';

// Define types for the API response
interface StockSentimentItem {
  symbol: string;
  sentiment_score: number;
  date: string;
}

interface TopBottomStocksResponse {
  top_20: StockSentimentItem[];
  bottom_20: StockSentimentItem[];
}

const TopBottomSentiment: React.FC = () => {
  // State for storing the fetched data
  const [data, setData] = useState<TopBottomStocksResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Function to format date
  const formatDate = (dateString: string): string => {
    const options: Intl.DateTimeFormatOptions = { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };

  // Fetch data when component mounts
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await axios.get<TopBottomStocksResponse>(
          // Correct backend route (stocks router is already prefixed with `/stocks`)
          `${import.meta.env.VITE_API_URL}/api/v1/stocks/top-bottom-20`
        );
        setData(response.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching sentiment data:', err);
        // If the API request fails, use mock data for demonstration
        const mockData: TopBottomStocksResponse = {
          top_20: [
            { symbol: 'AAPL', sentiment_score: 0.95, date: '2025-06-12' },
            { symbol: 'MSFT', sentiment_score: 0.92, date: '2025-06-12' },
            { symbol: 'GOOGL', sentiment_score: 0.88, date: '2025-06-12' },
            { symbol: 'AMZN', sentiment_score: 0.85, date: '2025-06-12' },
            { symbol: 'TSLA', sentiment_score: 0.82, date: '2025-06-12' },
            { symbol: 'META', sentiment_score: 0.79, date: '2025-06-12' },
            { symbol: 'NVDA', sentiment_score: 0.77, date: '2025-06-12' },
            { symbol: 'NFLX', sentiment_score: 0.75, date: '2025-06-12' },
            { symbol: 'PYPL', sentiment_score: 0.72, date: '2025-06-12' },
            { symbol: 'INTC', sentiment_score: 0.70, date: '2025-06-12' }
          ],
          bottom_20: [
            { symbol: 'XRX', sentiment_score: -0.68, date: '2025-06-12' },
            { symbol: 'GME', sentiment_score: -0.72, date: '2025-06-12' },
            { symbol: 'AMC', sentiment_score: -0.75, date: '2025-06-12' },
            { symbol: 'BBBY', sentiment_score: -0.78, date: '2025-06-12' },
            { symbol: 'NKLA', sentiment_score: -0.80, date: '2025-06-12' },
            { symbol: 'RIDE', sentiment_score: -0.83, date: '2025-06-12' },
            { symbol: 'WISH', sentiment_score: -0.85, date: '2025-06-12' },
            { symbol: 'CLOV', sentiment_score: -0.87, date: '2025-06-12' },
            { symbol: 'PLTR', sentiment_score: -0.90, date: '2025-06-12' },
            { symbol: 'SPCE', sentiment_score: -0.92, date: '2025-06-12' }
          ]
        };
        setData(mockData);
        // Inform the user we're using mock data
        setError('API is unavailable. Using demo data for display purposes.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Render loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-4 text-gray-600">Loading sentiment data...</p>
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

  // Render data
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">Market Sentiment Analysis</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Top 20 Stocks */}
        <div className="bg-green-50 rounded-lg p-4 border border-green-100">
          <h3 className="text-lg font-semibold text-green-800 mb-4 flex items-center">
            <svg 
              className="w-5 h-5 mr-2" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24" 
              xmlns="http://www.w3.org/2000/svg"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth="2" 
                d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
              />
            </svg>
            Top 20 Stocks by Sentiment
          </h3>
          
          <div className="overflow-y-auto max-h-[500px]">
            <table className="min-w-full">
              <thead className="bg-green-100">
                <tr>
                  <th className="py-2 px-4 text-left text-xs font-medium text-green-800 uppercase tracking-wider">Symbol</th>
                  <th className="py-2 px-4 text-left text-xs font-medium text-green-800 uppercase tracking-wider">Score</th>
                  <th className="py-2 px-4 text-left text-xs font-medium text-green-800 uppercase tracking-wider">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-green-100">
                {data?.top_20.map((stock, index) => (
                  <tr key={`${stock.symbol}-${index}`} className="hover:bg-green-100/50">
                    <td className="py-2 px-4 text-sm font-medium text-gray-900">{stock.symbol}</td>
                    <td className="py-2 px-4 text-sm text-green-700">
                      {stock.sentiment_score.toFixed(2)}
                    </td>
                    <td className="py-2 px-4 text-sm text-gray-500">{formatDate(stock.date)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        
        {/* Bottom 20 Stocks */}
        <div className="bg-red-50 rounded-lg p-4 border border-red-100">
          <h3 className="text-lg font-semibold text-red-800 mb-4 flex items-center">
            <svg 
              className="w-5 h-5 mr-2" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24" 
              xmlns="http://www.w3.org/2000/svg"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth="2" 
                d="M13 17h8m0 0v-8m0 8l-8-8-4 4-6-6"
              />
            </svg>
            Bottom 20 Stocks by Sentiment
          </h3>
          
          <div className="overflow-y-auto max-h-[500px]">
            <table className="min-w-full">
              <thead className="bg-red-100">
                <tr>
                  <th className="py-2 px-4 text-left text-xs font-medium text-red-800 uppercase tracking-wider">Symbol</th>
                  <th className="py-2 px-4 text-left text-xs font-medium text-red-800 uppercase tracking-wider">Score</th>
                  <th className="py-2 px-4 text-left text-xs font-medium text-red-800 uppercase tracking-wider">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-red-100">
                {data?.bottom_20.map((stock, index) => (
                  <tr key={`${stock.symbol}-${index}`} className="hover:bg-red-100/50">
                    <td className="py-2 px-4 text-sm font-medium text-gray-900">{stock.symbol}</td>
                    <td className="py-2 px-4 text-sm text-red-700">
                      {stock.sentiment_score.toFixed(2)}
                    </td>
                    <td className="py-2 px-4 text-sm text-gray-500">{formatDate(stock.date)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TopBottomSentiment;
