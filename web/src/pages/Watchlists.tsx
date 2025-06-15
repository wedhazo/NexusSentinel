import React, { useState, useEffect } from 'react';
import { getWatchlistItems, addToWatchlist, removeFromWatchlist } from '../api/watchlistApi';
import { WatchlistItem } from '../types/apiTypes';

const Watchlists: React.FC = () => {
  // State variables
  const [watchlistItems, setWatchlistItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [symbol, setSymbol] = useState<string>('');
  const [addingSymbol, setAddingSymbol] = useState<boolean>(false);
  const [addError, setAddError] = useState<string | null>(null);
  const [removingSymbols, setRemovingSymbols] = useState<Set<string>>(new Set());

  // Fetch watchlist items when component mounts
  useEffect(() => {
    const fetchWatchlist = async () => {
      try {
        setLoading(true);
        setError(null);
        const items = await getWatchlistItems();
        setWatchlistItems(items);
      } catch (err: any) {
        console.error('Error fetching watchlist:', err);
        setError(err.message || 'Failed to load watchlist. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchWatchlist();
  }, []);

  // Handle adding a stock to the watchlist
  const handleAddToWatchlist = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!symbol.trim()) {
      setAddError('Please enter a stock symbol');
      return;
    }

    try {
      setAddingSymbol(true);
      setAddError(null);
      const newItem = await addToWatchlist(symbol.trim().toUpperCase());
      setWatchlistItems(prev => [newItem, ...prev]);
      setSymbol('');
    } catch (err: any) {
      console.error('Error adding to watchlist:', err);
      setAddError(err.message || 'Failed to add stock to watchlist. Please try again.');
    } finally {
      setAddingSymbol(false);
    }
  };

  // Handle removing a stock from the watchlist
  const handleRemoveFromWatchlist = async (symbol: string) => {
    try {
      setRemovingSymbols(prev => new Set(prev).add(symbol));
      await removeFromWatchlist(symbol);
      setWatchlistItems(prev => prev.filter(item => item.symbol !== symbol));
    } catch (err: any) {
      console.error('Error removing from watchlist:', err);
      // Show error in a toast or alert
    } finally {
      setRemovingSymbols(prev => {
        const updated = new Set(prev);
        updated.delete(symbol);
        return updated;
      });
    }
  };

  // Format date for display
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Get CSS class for sentiment score
  const getSentimentClass = (score?: number): string => {
    if (score === undefined || score === null) return 'text-gray-500';
    if (score > 0.3) return 'text-green-600 font-medium';
    if (score > 0) return 'text-green-500';
    if (score > -0.3) return 'text-red-500';
    return 'text-red-600 font-medium';
  };

  // Format sentiment score for display
  const formatSentiment = (score?: number): string => {
    if (score === undefined || score === null) return 'N/A';
    return score.toFixed(2);
  };

  // Render loading state
  if (loading && watchlistItems.length === 0) {
    return (
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">My Watchlist</h1>
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="flex flex-col items-center">
            <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <p className="mt-4 text-gray-600">Loading watchlist...</p>
          </div>
        </div>
      </div>
    );
  }

  // Render error state
  if (error && watchlistItems.length === 0) {
    return (
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">My Watchlist</h1>
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
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">My Watchlist</h1>
      
      {/* Add to Watchlist Form */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Add Stock to Watchlist</h2>
        <form onSubmit={handleAddToWatchlist} className="flex flex-col sm:flex-row gap-4">
          <div className="flex-grow">
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              placeholder="Enter stock symbol (e.g., AAPL)"
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={addingSymbol}
            />
            {addError && (
              <p className="mt-1 text-sm text-red-600">{addError}</p>
            )}
          </div>
          <button
            type="submit"
            disabled={addingSymbol || !symbol.trim()}
            className={`px-6 py-2 rounded-md text-white font-medium ${
              addingSymbol || !symbol.trim()
                ? 'bg-blue-300 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {addingSymbol ? (
              <div className="flex items-center">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                <span>Adding...</span>
              </div>
            ) : (
              'Add to Watchlist'
            )}
          </button>
        </form>
      </div>
      
      {/* Watchlist Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Symbol
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Company
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Sentiment
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date Added
                </th>
                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {watchlistItems.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                    <svg 
                      className="w-12 h-12 text-gray-300 mx-auto mb-4" 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24" 
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                        strokeWidth="2" 
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    <p className="text-lg">Your watchlist is empty</p>
                    <p className="text-sm mt-2">Add stocks using the form above</p>
                  </td>
                </tr>
              ) : (
                watchlistItems.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-lg font-bold text-blue-600">{item.symbol}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{item.company_name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`text-sm ${getSentimentClass(item.sentiment_score)}`}>
                        {item.sentiment_score !== undefined && item.sentiment_score > 0 ? '+' : ''}
                        {formatSentiment(item.sentiment_score)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">{formatDate(item.date_added)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <button
                        onClick={() => handleRemoveFromWatchlist(item.symbol)}
                        disabled={removingSymbols.has(item.symbol)}
                        className={`px-3 py-1 rounded-md text-sm font-medium ${
                          removingSymbols.has(item.symbol)
                            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                            : 'bg-red-100 text-red-600 hover:bg-red-200'
                        }`}
                      >
                        {removingSymbols.has(item.symbol) ? (
                          <div className="flex items-center">
                            <div className="w-3 h-3 border-2 border-red-600 border-t-transparent rounded-full animate-spin mr-1"></div>
                            <span>Removing...</span>
                          </div>
                        ) : (
                          'Remove'
                        )}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Loading indicator when refreshing */}
      {loading && watchlistItems.length > 0 && (
        <div className="flex justify-center mt-6">
          <div className="flex items-center">
            <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mr-2"></div>
            <span className="text-sm text-gray-600">Refreshing watchlist...</span>
          </div>
        </div>
      )}
      
      {/* Error message when refresh fails */}
      {error && watchlistItems.length > 0 && (
        <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-2 text-sm text-red-700 hover:text-red-800 underline"
          >
            Refresh page
          </button>
        </div>
      )}
    </div>
  );
};

export default Watchlists;
