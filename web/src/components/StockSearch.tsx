import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

// Types for stock data
interface StockItem {
  symbol: string;
  name: string;
  exchange?: string;
  sector?: string;
}

interface StockSearchProps {
  onSelectStock?: (stock: StockItem) => void;
}

const StockSearch: React.FC<StockSearchProps> = ({ onSelectStock }) => {
  // State for search input and results
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<StockItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [showDropdown, setShowDropdown] = useState<boolean>(false);
  const [recentSearches, setRecentSearches] = useState<StockItem[]>([]);
  
  // Ref for dropdown and input
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Popular stocks (predefined)
  const popularStocks: StockItem[] = [
    { symbol: 'AAPL', name: 'Apple Inc.' },
    { symbol: 'MSFT', name: 'Microsoft Corporation' },
    { symbol: 'GOOGL', name: 'Alphabet Inc.' },
    { symbol: 'AMZN', name: 'Amazon.com Inc.' },
    { symbol: 'TSLA', name: 'Tesla, Inc.' },
    { symbol: 'META', name: 'Meta Platforms, Inc.' },
    { symbol: 'NVDA', name: 'NVIDIA Corporation' },
    { symbol: 'JPM', name: 'JPMorgan Chase & Co.' },
  ];

  // Load recent searches from localStorage on component mount
  useEffect(() => {
    const savedSearches = localStorage.getItem('recentStockSearches');
    if (savedSearches) {
      try {
        setRecentSearches(JSON.parse(savedSearches));
      } catch (error) {
        console.error('Failed to parse recent searches:', error);
        localStorage.removeItem('recentStockSearches');
      }
    }
  }, []);

  // Handle clicks outside the dropdown to close it
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current && 
        !dropdownRef.current.contains(event.target as Node) &&
        inputRef.current && 
        !inputRef.current.contains(event.target as Node)
      ) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Search for stocks when query changes
  useEffect(() => {
    const searchStocks = async () => {
      if (!searchQuery.trim()) {
        setSearchResults([]);
        return;
      }

      setIsLoading(true);
      try {
        // In a real implementation, you would fetch from your API:
        // const response = await axios.get(`${import.meta.env.VITE_API_URL}/api/v1/stocks/search?q=${searchQuery}`);
        // setSearchResults(response.data);
        
        // Mock search results for development
        const query = searchQuery.toLowerCase();
        
        // Simulate API response delay
        await new Promise(resolve => setTimeout(resolve, 300));
        
        // Filter stocks that match the query
        const mockResults = [
          { symbol: 'AAPL', name: 'Apple Inc.', exchange: 'NASDAQ', sector: 'Technology' },
          { symbol: 'MSFT', name: 'Microsoft Corporation', exchange: 'NASDAQ', sector: 'Technology' },
          { symbol: 'AMZN', name: 'Amazon.com Inc.', exchange: 'NASDAQ', sector: 'Consumer Cyclical' },
          { symbol: 'GOOGL', name: 'Alphabet Inc.', exchange: 'NASDAQ', sector: 'Communication Services' },
          { symbol: 'META', name: 'Meta Platforms, Inc.', exchange: 'NASDAQ', sector: 'Communication Services' },
          { symbol: 'TSLA', name: 'Tesla, Inc.', exchange: 'NASDAQ', sector: 'Consumer Cyclical' },
          { symbol: 'NVDA', name: 'NVIDIA Corporation', exchange: 'NASDAQ', sector: 'Technology' },
          { symbol: 'JPM', name: 'JPMorgan Chase & Co.', exchange: 'NYSE', sector: 'Financial Services' },
          { symbol: 'V', name: 'Visa Inc.', exchange: 'NYSE', sector: 'Financial Services' },
          { symbol: 'JNJ', name: 'Johnson & Johnson', exchange: 'NYSE', sector: 'Healthcare' },
          { symbol: 'WMT', name: 'Walmart Inc.', exchange: 'NYSE', sector: 'Consumer Defensive' },
          { symbol: 'PG', name: 'Procter & Gamble Co.', exchange: 'NYSE', sector: 'Consumer Defensive' },
          { symbol: 'MA', name: 'Mastercard Inc.', exchange: 'NYSE', sector: 'Financial Services' },
          { symbol: 'UNH', name: 'UnitedHealth Group Inc.', exchange: 'NYSE', sector: 'Healthcare' },
          { symbol: 'HD', name: 'Home Depot Inc.', exchange: 'NYSE', sector: 'Consumer Cyclical' },
          { symbol: 'BAC', name: 'Bank of America Corp.', exchange: 'NYSE', sector: 'Financial Services' },
          { symbol: 'PFE', name: 'Pfizer Inc.', exchange: 'NYSE', sector: 'Healthcare' },
          { symbol: 'ADBE', name: 'Adobe Inc.', exchange: 'NASDAQ', sector: 'Technology' },
          { symbol: 'NFLX', name: 'Netflix Inc.', exchange: 'NASDAQ', sector: 'Communication Services' },
          { symbol: 'DIS', name: 'Walt Disney Co.', exchange: 'NYSE', sector: 'Communication Services' },
        ].filter(stock => 
          stock.symbol.toLowerCase().includes(query) || 
          stock.name.toLowerCase().includes(query)
        ).slice(0, 10); // Limit to 10 results
        
        setSearchResults(mockResults);
      } catch (error) {
        console.error('Error searching for stocks:', error);
        setSearchResults([]);
      } finally {
        setIsLoading(false);
      }
    };

    // Debounce search to avoid too many requests
    const timeoutId = setTimeout(() => {
      searchStocks();
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  // Handle selecting a stock
  const handleSelectStock = (stock: StockItem) => {
    // Call the onSelectStock callback if provided
    if (onSelectStock) {
      onSelectStock(stock);
    }
    
    // Update search input
    setSearchQuery(stock.symbol);
    setShowDropdown(false);
    
    // Add to recent searches (avoid duplicates)
    const updatedRecentSearches = [
      stock,
      ...recentSearches.filter(item => item.symbol !== stock.symbol)
    ].slice(0, 5); // Keep only 5 most recent
    
    setRecentSearches(updatedRecentSearches);
    localStorage.setItem('recentStockSearches', JSON.stringify(updatedRecentSearches));
  };

  // Clear recent searches
  const clearRecentSearches = (e: React.MouseEvent) => {
    e.stopPropagation();
    setRecentSearches([]);
    localStorage.removeItem('recentStockSearches');
  };

  return (
    <div className="relative w-full">
      {/* Search Input */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <input
          ref={inputRef}
          type="text"
          className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          placeholder="Search for stocks (e.g., AAPL, Microsoft)"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onFocus={() => setShowDropdown(true)}
          aria-expanded={showDropdown}
          aria-autocomplete="list"
          aria-controls="stock-search-results"
        />
        {searchQuery && (
          <button
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
            onClick={() => {
              setSearchQuery('');
              inputRef.current?.focus();
            }}
          >
            <svg className="h-5 w-5 text-gray-400 hover:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
      
      {/* Search Results Dropdown */}
      {showDropdown && (
        <div
          ref={dropdownRef}
          id="stock-search-results"
          className="absolute z-10 mt-1 w-full bg-white shadow-lg rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm max-h-60"
        >
          {isLoading ? (
            <div className="flex items-center justify-center py-4">
              <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              <span className="ml-2 text-gray-600">Searching...</span>
            </div>
          ) : (
            <>
              {/* Search Results */}
              {searchQuery && searchResults.length > 0 && (
                <div className="px-3 py-2">
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                    Search Results
                  </h3>
                  <ul className="space-y-1">
                    {searchResults.map((stock) => (
                      <li key={stock.symbol}>
                        <button
                          className="flex items-center w-full px-3 py-2 text-left rounded-md hover:bg-gray-100"
                          onClick={() => handleSelectStock(stock)}
                        >
                          <div className="flex-1">
                            <div className="flex items-center">
                              <span className="font-medium text-gray-900">{stock.symbol}</span>
                              {stock.exchange && (
                                <span className="ml-2 text-xs text-gray-500">{stock.exchange}</span>
                              )}
                            </div>
                            <p className="text-sm text-gray-600">{stock.name}</p>
                          </div>
                          {stock.sector && (
                            <span className="text-xs text-gray-500">{stock.sector}</span>
                          )}
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {/* Recent Searches */}
              {recentSearches.length > 0 && (
                <div className="px-3 py-2 border-t border-gray-100">
                  <div className="flex justify-between items-center mb-2">
                    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Recent Searches
                    </h3>
                    <button
                      className="text-xs text-blue-600 hover:text-blue-800"
                      onClick={clearRecentSearches}
                    >
                      Clear
                    </button>
                  </div>
                  <ul className="space-y-1">
                    {recentSearches.map((stock) => (
                      <li key={stock.symbol}>
                        <button
                          className="flex items-center w-full px-3 py-2 text-left rounded-md hover:bg-gray-100"
                          onClick={() => handleSelectStock(stock)}
                        >
                          <div className="flex items-center">
                            <svg className="h-4 w-4 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span className="font-medium text-gray-900">{stock.symbol}</span>
                            <span className="ml-2 text-sm text-gray-600">{stock.name}</span>
                          </div>
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {/* Popular Stocks */}
              {(!searchQuery || searchResults.length === 0) && (
                <div className={`px-3 py-2 ${recentSearches.length > 0 ? 'border-t border-gray-100' : ''}`}>
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                    Popular Stocks
                  </h3>
                  <div className="grid grid-cols-2 gap-2">
                    {popularStocks.map((stock) => (
                      <button
                        key={stock.symbol}
                        className="flex items-center px-3 py-2 text-left rounded-md hover:bg-gray-100"
                        onClick={() => handleSelectStock(stock)}
                      >
                        <div>
                          <span className="font-medium text-gray-900">{stock.symbol}</span>
                          <p className="text-sm text-gray-600 truncate">{stock.name}</p>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
              
              {/* No Results */}
              {searchQuery && searchResults.length === 0 && (
                <div className="px-3 py-6 text-center">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No results found</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Try a different search term or browse popular stocks.
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default StockSearch;
