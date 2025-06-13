import React, { useState, useEffect } from 'react';
// React-Query hooks
import {
  useWatchlists,
  useCreateWatchlist,
  Watchlist as ApiWatchlist,
} from '../lib/api';
// Zustand store
import useWatchlistStore from '../store/watchlistStore';
// shadcn/ui components
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { ScrollArea } from '../components/ui/scroll-area';

// Types for watchlist data
interface Stock {
  symbol: string;
  company_name?: string;
}

interface NewWatchlist {
  name: string;
  description?: string;
  stock_symbols: string[];
}

const Watchlists: React.FC = () => {
  // Zustand store bindings
  const { watchlists, setWatchlists } = useWatchlistStore((state) => ({
    watchlists: state.watchlists,
    setWatchlists: state.setWatchlists,
  }));

  // React-Query: fetch watchlists
  const {
    data: fetchedWatchlists,
    isLoading,
    error,
  } = useWatchlists();

  // Sync fetched data into Zustand
  useEffect(() => {
    if (fetchedWatchlists) {
      setWatchlists(fetchedWatchlists as ApiWatchlist[]);
    }
  }, [fetchedWatchlists, setWatchlists]);
  
  // State for the new watchlist form
  const [showForm, setShowForm] = useState<boolean>(false);
  const [newWatchlist, setNewWatchlist] = useState<NewWatchlist>({
    name: '',
    description: '',
    stock_symbols: []
  });
  const [stockSymbolInput, setStockSymbolInput] = useState<string>('');
  const [formSubmitting, setFormSubmitting] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  // React-Query mutation for create
  const createMutation = useCreateWatchlist();

  // Handle form input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setNewWatchlist(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Add stock symbol to the list
  const addStockSymbol = () => {
    if (!stockSymbolInput.trim()) return;
    
    // Convert to uppercase and check if already in the list
    const symbol = stockSymbolInput.trim().toUpperCase();
    if (newWatchlist.stock_symbols.includes(symbol)) {
      setFormError('This symbol is already in the list');
      return;
    }
    
    setNewWatchlist(prev => ({
      ...prev,
      stock_symbols: [...prev.stock_symbols, symbol]
    }));
    setStockSymbolInput('');
    setFormError(null);
  };

  // Remove stock symbol from the list
  const removeStockSymbol = (symbol: string) => {
    setNewWatchlist(prev => ({
      ...prev,
      stock_symbols: prev.stock_symbols.filter(s => s !== symbol)
    }));
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newWatchlist.name.trim()) {
      setFormError('Watchlist name is required');
      return;
    }
    
    try {
      setFormSubmitting(true);
      setFormError(null);
      
      // Submit using react-query mutation
      await createMutation.mutateAsync(newWatchlist);
      
      // Reset form
      setNewWatchlist({
        name: '',
        description: '',
        stock_symbols: []
      });
      setShowForm(false);
    } catch (err: any) {
      console.error('Error creating watchlist:', err);
      setFormError(
        err.response?.data?.detail || 
        'Failed to create watchlist. Please try again.'
      );
    } finally {
      setFormSubmitting(false);
    }
  };

  // Render loading state
  if (isLoading && watchlists.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-4 text-gray-600">Loading watchlists...</p>
        </div>
      </div>
    );
  }

  // Render error state
  if (error && watchlists.length === 0) {
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
        <p className="text-red-600">{(error as Error)?.message || 'An error occurred'}</p>
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
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Watchlists</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          {showForm ? 'Cancel' : 'Create Watchlist'}
        </button>
      </div>
      
      {/* Create Watchlist Form */}
      {showForm && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Create New Watchlist</h2>
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                Watchlist Name *
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={newWatchlist.name}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="My Watchlist"
                required
              />
            </div>
            
            <div className="mb-4">
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                Description (Optional)
              </label>
              <textarea
                id="description"
                name="description"
                value={newWatchlist.description}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="A description of your watchlist"
                rows={3}
              />
            </div>
            
            <div className="mb-4">
              <label htmlFor="stockSymbol" className="block text-sm font-medium text-gray-700 mb-1">
                Add Stock Symbols
              </label>
              <div className="flex">
                <input
                  type="text"
                  id="stockSymbol"
                  value={stockSymbolInput}
                  onChange={(e) => setStockSymbolInput(e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="AAPL"
                />
                <button
                  type="button"
                  onClick={addStockSymbol}
                  className="px-4 py-2 bg-gray-200 text-gray-800 rounded-r-md hover:bg-gray-300 transition-colors"
                >
                  Add
                </button>
              </div>
              
              {/* Stock symbols list */}
              {newWatchlist.stock_symbols.length > 0 && (
                <div className="mt-3">
                  <p className="text-sm font-medium text-gray-700 mb-2">Selected Stocks:</p>
                  <div className="flex flex-wrap gap-2">
                    {newWatchlist.stock_symbols.map(symbol => (
                      <div 
                        key={symbol} 
                        className="inline-flex items-center bg-blue-100 text-blue-800 px-2 py-1 rounded-md"
                      >
                        <span>{symbol}</span>
                        <button
                          type="button"
                          onClick={() => removeStockSymbol(symbol)}
                          className="ml-1 text-blue-600 hover:text-blue-800"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                          </svg>
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            {formError && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-600">{formError}</p>
              </div>
            )}
            
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={formSubmitting}
                className={`px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors ${
                  formSubmitting ? 'opacity-75 cursor-not-allowed' : ''
                }`}
              >
                {formSubmitting ? 'Creating...' : 'Create Watchlist'}
              </button>
            </div>
          </form>
        </div>
      )}
      
      {/* Watchlists Grid */}
      {watchlists.length === 0 ? (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
          <svg 
            className="w-16 h-16 text-gray-400 mx-auto mb-4" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24" 
            xmlns="http://www.w3.org/2000/svg"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth="2" 
              d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="text-lg font-medium text-gray-800 mb-2">No Watchlists Found</h3>
          <p className="text-gray-600 mb-4">Create your first watchlist to start tracking stocks.</p>
          {!showForm && (
            <button
              onClick={() => setShowForm(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Create Watchlist
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {watchlists.map((watchlist) => (
            <Card 
              key={watchlist.watchlist_id}
              className="overflow-hidden hover:shadow-lg transition-shadow"
            >
              <CardHeader>
                <CardTitle>{watchlist.name}</CardTitle>
                {watchlist.description && (
                  <CardDescription className="line-clamp-2">
                    {watchlist.description}
                  </CardDescription>
                )}
              </CardHeader>
              
              <CardContent>
                <div className="flex items-center text-gray-500 mb-4">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
                  </svg>
                  <span>{watchlist.stocks.length} {watchlist.stocks.length === 1 ? 'Stock' : 'Stocks'}</span>
                </div>
                
                {watchlist.stocks.length > 0 && (
                  <div className="mb-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">Symbols:</p>
                    <div className="flex flex-wrap gap-1">
                      {watchlist.stocks.slice(0, 5).map(stock => (
                        <Badge
                          key={stock.symbol}
                          variant="stock"
                          size="sm"
                        >
                          {stock.symbol}
                        </Badge>
                      ))}
                      {watchlist.stocks.length > 5 && (
                        <Badge variant="neutral" size="sm">
                          +{watchlist.stocks.length - 5} more
                        </Badge>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
              
              <CardFooter className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">
                  Created: {new Date(watchlist.created_at).toLocaleDateString()}
                </span>
                <button
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  onClick={() => {
                    /* View watchlist details */
                  }}
                >
                  View
                </button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default Watchlists;
