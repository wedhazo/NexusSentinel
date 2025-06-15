import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../api/apiClient';
import { StockSearchResult, StockSearchResponse } from '../types/apiTypes';
import { useNavigate } from 'react-router-dom';

const StockSearch: React.FC = () => {
  // State variables
  const [query, setQuery] = useState<string>('');
  const [results, setResults] = useState<StockSearchResult[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showResults, setShowResults] = useState<boolean>(false);
  
  // For navigation to stock detail pages
  const navigate = useNavigate();

  // Debounced search function
  const debouncedSearch = useCallback(
    (() => {
      let timeout: NodeJS.Timeout | null = null;
      
      return (searchQuery: string) => {
        if (timeout) {
          clearTimeout(timeout);
        }
        
        timeout = setTimeout(async () => {
          if (searchQuery.trim().length >= 2) {
            try {
              setLoading(true);
              setError(null);
              
              // Fetch search results from API
              const response = await api.get<StockSearchResponse>(
                `/stocks?search=${encodeURIComponent(searchQuery)}&limit=10`
              );
              
              setResults(response.results);
              setShowResults(true);
            } catch (err: any) {
              console.error('Error searching stocks:', err);
              setError(err.message || 'Failed to search stocks. Please try again.');
              setResults([]);
            } finally {
              setLoading(false);
            }
          } else {
            setResults([]);
            setShowResults(false);
          }
        }, 300); // 300ms debounce
      };
    })(),
    []
  );

  // Update search when query changes
  useEffect(() => {
    if (query.trim().length >= 2) {
      debouncedSearch(query);
    } else {
      setResults([]);
      setShowResults(false);
    }
  }, [query, debouncedSearch]);

  // Handle click outside to close results
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest('.stock-search-container')) {
        setShowResults(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Navigate to stock detail page
  const handleSelectStock = (symbol: string) => {
    navigate(`/stocks/${symbol}`);
    setQuery('');
    setShowResults(false);
  };

  // Format price change with color and sign
  const formatPriceChange = (change?: number) => {
    if (change === undefined) return null;
    
    const isPositive = change >= 0;
    const textColor = isPositive ? 'text-green-600' : 'text-red-600';
    
    return (
      <span className={`text-sm font-medium ${textColor}`}>
        {isPositive ? '+' : ''}{change.toFixed(2)}%
      </span>
    );
  };

  // Format sentiment score with color
  const formatSentiment = (score?: number) => {
    if (score === undefined) return null;
    
    let textColor = 'text-gray-600';
    if (score > 0.3) textColor = 'text-green-600';
    else if (score < -0.3) textColor = 'text-red-600';
    
    return (
      <span className={`text-sm font-medium ${textColor}`}>
        {score.toFixed(2)}
      </span>
    );
  };

  return (
    <div className="stock-search-container relative w-full max-w-lg mx-auto">
      {/* Search Input */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
          <svg
            className="w-5 h-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
        <input
          type="text"
          className="w-full p-4 pl-10 text-sm text-gray-900 border border-gray-300 rounded-lg bg-white focus:ring-blue-500 focus:border-blue-500"
          placeholder="Search for a stock by symbol or company name..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => {
            if (results.length > 0) {
              setShowResults(true);
            }
          }}
        />
        {loading && (
          <div className="absolute inset-y-0 right-0 flex items-center pr-3">
            <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          </div>
        )}
      </div>

      {/* Search Results */}
      {showResults && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-96 overflow-y-auto">
          {error && (
            <div className="p-4 text-sm text-red-600 bg-red-50">
              <p>{error}</p>
            </div>
          )}

          {!error && results.length === 0 && !loading && (
            <div className="p-4 text-sm text-gray-500">
              <p>No stocks found. Try a different search term.</p>
            </div>
          )}

          {results.length > 0 && (
            <ul className="divide-y divide-gray-200">
              {results.map((stock) => (
                <li
                  key={stock.symbol}
                  className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => handleSelectStock(stock.symbol)}
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-lg font-bold text-gray-900">{stock.symbol}</p>
                      <p className="text-sm text-gray-600">{stock.company_name}</p>
                      {stock.exchange && (
                        <p className="text-xs text-gray-500">{stock.exchange}</p>
                      )}
                    </div>
                    <div className="text-right">
                      {stock.current_price !== undefined && (
                        <p className="text-lg font-semibold text-gray-900">
                          ${stock.current_price.toFixed(2)}
                        </p>
                      )}
                      {formatPriceChange(stock.price_change_percent)}
                      {stock.sentiment_score !== undefined && (
                        <div className="mt-1 text-xs text-gray-500">
                          Sentiment: {formatSentiment(stock.sentiment_score)}
                        </div>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};

export default StockSearch;
